import SwiftUI
import AVKit
import Photos
import QuickLook


private let laapLogger = AppLogger(category: "LaapMedia")
// MARK: - laap:// Media Provider

// MARK: Media Cache — avoids re-loading/decoding when LazyVStack recycles cells

final class LaapMediaCache {
    static let shared = LaapMediaCache()

    /// Downsampled UIImage cache keyed by absolute laap:// URL string.
    private let imageCache = NSCache<NSString, UIImage>()
    /// Video thumbnail cache keyed by file path.
    private let thumbnailCache = NSCache<NSString, UIImage>()
    /// Resolved host file URL cache keyed by laap:// URL string.
    private let resolvedURLCache = NSCache<NSString, NSURL>()

    private init() {
        imageCache.countLimit = 50
        thumbnailCache.countLimit = 30
    }

    func image(for key: String) -> UIImage? {
        imageCache.object(forKey: key as NSString)
    }

    func setImage(_ image: UIImage, for key: String) {
        imageCache.setObject(image, forKey: key as NSString)
    }

    func thumbnail(for key: String) -> UIImage? {
        thumbnailCache.object(forKey: key as NSString)
    }

    func setThumbnail(_ image: UIImage, for key: String) {
        thumbnailCache.setObject(image, forKey: key as NSString)
    }

    func resolvedURL(for key: String) -> URL? {
        resolvedURLCache.object(forKey: key as NSString) as URL?
    }

    func setResolvedURL(_ url: URL, for key: String) {
        resolvedURLCache.setObject(url as NSURL, forKey: key as NSString)
    }
}

/// Downsample an image from data using ImageIO to avoid decoding the full bitmap.
func downsampleImage(data: Data, maxPixelSize: CGFloat = 2048) -> UIImage? {
    let options: [CFString: Any] = [
        kCGImageSourceShouldCache: false
    ]
    guard let source = CGImageSourceCreateWithData(data as CFData, options as CFDictionary) else { return nil }
    let downsampleOptions: [CFString: Any] = [
        kCGImageSourceCreateThumbnailFromImageAlways: true,
        kCGImageSourceShouldCacheImmediately: true,
        kCGImageSourceCreateThumbnailWithTransform: true,
        kCGImageSourceThumbnailMaxPixelSize: maxPixelSize
    ]
    guard let cgImage = CGImageSourceCreateThumbnailAtIndex(source, 0, downsampleOptions as CFDictionary) else {
        // Fallback: try full decode for formats ImageIO can't thumbnail
        return UIImage(data: data)
    }
    return UIImage(cgImage: cgImage)
}

/// Resolve a laap:// URL with caching to avoid repeated FileManager lookups.
///
/// Cache key is scoped by the active session id because per-session paths
/// (e.g. `laap://attachments/foo.png`) resolve to different files in
/// `Library/LaapChat/laap/<sessionId>/…` depending on which session is
/// active. Keying on `url.absoluteString` alone caused cross-session hits
/// where a bubble in session B resolved to session A's file.
func resolveLaapFileURLCached(url: URL) -> URL? {
    let sessionScope = AIChatViewModel.activeSessionId ?? "nil"
    let key = "\(sessionScope)|\(url.absoluteString)"
    if let cached = LaapMediaCache.shared.resolvedURL(for: key) {
        laapLogger.info("[LaapImage][ResolveCache] HIT url=\(url.absoluteString) → \(cached.path)")
        return cached
    }
    if let resolved = resolveLaapFileURL(url: url) {
        LaapMediaCache.shared.setResolvedURL(resolved, for: key)
        laapLogger.info("[LaapImage][ResolveCache] MISS→resolved url=\(url.absoluteString) → \(resolved.path)")
        return resolved
    }
    laapLogger.warning("[LaapImage][ResolveCache] MISS→nil url=\(url.absoluteString)")
    return nil
}

/// Fingerprint-based cache key for a media source string. Combines the
/// source URL with the underlying file's size + mtime so in-memory image
/// caches naturally invalidate whenever the file on disk is rewritten
/// (e.g. the agent regenerates a chart at the same path).
///
/// For `laap://` sources we resolve to the host file URL and stat it.
/// For `http(s)://` and anything we can't resolve we fall back to the
/// plain source string — remote caches are managed by URL loading layers
/// above us, and a stale in-memory hit there is acceptable for this tool.
/// Returns `nil` only when the source cannot be parsed as a URL.
func laapMediaCacheKey(for source: String) -> String {
    guard let url = URL(string: source) else { return source }
    return laapMediaCacheKey(for: url)
}

func laapMediaCacheKey(for url: URL) -> String {
    let base = url.absoluteString
    // Non-laap schemes: return as-is, we don't own that file's lifecycle.
    guard url.scheme == "laap" else { return base }
    guard let fileURL = resolveLaapFileURLCached(url: url) else {
        // File not resolvable (yet) — use the base key so a later real
        // fingerprint load replaces it naturally.
        return base
    }
    // Stat without going through FileManager's attribute wrapper — it
    // allocates a dictionary and is measurably slower.
    var st = stat()
    guard stat(fileURL.path, &st) == 0 else { return base }
    // Seconds + nanoseconds (APFS has nanosecond-resolution mtime, HFS+
    // only seconds — either way we capture every rewrite we care about).
    let secs = st.st_mtimespec.tv_sec
    let nsecs = st.st_mtimespec.tv_nsec
    let size = st.st_size
    return "\(base)|\(size)|\(secs).\(nsecs)"
}

/// Standard placeholder height for media items to prevent layout jumps
/// when LazyVStack recycles cells and images load asynchronously.
let mediaPlaceholderHeight: CGFloat = 200

let laapAudioExtensions: Set<String> = ["mp3", "m4a", "wav", "aac", "ogg", "flac"]
let laapVideoExtensions: Set<String> = ["mp4", "mov", "m4v", "avi", "mkv", "webm"]
let laapImageExtensions: Set<String> = ["png", "jpg", "jpeg", "gif", "webp", "bmp", "tiff"]
let laapTextExtensions: Set<String> = [
    "txt", "log", "json", "yaml", "yml", "toml", "xml", "plist",
    "csv", "tsv", "py", "swift", "js", "ts", "jsx", "tsx", "c", "cpp",
    "h", "rs", "go", "java", "rb", "sh", "bash", "zsh", "css", "sql",
    "conf", "ini", "cfg", "env", "gitignore", "dockerfile"
]
let laapMarkdownExtensions: Set<String> = ["md", "markdown"]
let laapHTMLExtensions: Set<String> = ["html", "htm", "svg"]
let laapDocumentExtensions: Set<String> = [
    "pdf",
    // Microsoft Office
    "doc", "docx", "xls", "xlsx", "ppt", "pptx",
    // iWork
    "pages", "numbers", "key",
    // Rich text
    "rtf", "rtfd",
]

/// Resolve a laap:// URL to a host filesystem URL.
/// Maps directly to persistent storage: Library/LaapChat/laap/<sessionId>/<subdir>/<path>
/// No dependency on iSH boot or bind mounts.
func resolveLaapFileURL(url: URL) -> URL? {
    guard let host = url.host else {
        laapLogger.warning("[ResolveLaapURL] no host in URL: \(url.absoluteString)")
        return nil
    }
    // Try the single-decoded subpath first; fall back to a double-decoded
    // variant when a link arrives double-encoded. [T-fix-double-encoding]
    let subPaths = LaapURLPathDecoding.subPathCandidates(for: url)

    let fm = FileManager.default

    // Primary: resolve via active session → persistent directory
    if let sid = AIChatViewModel.activeSessionId {
        for subPath in subPaths {
            let persistURL = AIChatViewModel.laapPersistentBase
                .appendingPathComponent(sid, isDirectory: true)
                .appendingPathComponent(host, isDirectory: true)
                .appendingPathComponent(subPath)
            let exists = fm.fileExists(atPath: persistURL.path)
            let fileSize: Int64 = exists ? ((try? fm.attributesOfItem(atPath: persistURL.path)[.size] as? Int64) ?? -1) : 0
            laapLogger.info("[LaapImage][Resolve] \(url.absoluteString) → session=\(sid) → \(persistURL.path) exists=\(exists) size=\(fileSize)")
            if exists { return persistURL }
        }
    }

    // Fallback: global directories (skills, memory) are not per-session
    let globalDirs: [(subdir: String, url: URL)] = [
        ("skills", AIChatViewModel.laapSkillsPersistentDir),
        ("memory", AIChatViewModel.laapMemoryPersistentDir),
        ("shared", AIChatViewModel.laapSharedPersistentDir),
    ]
    for (subdir, globalDir) in globalDirs where host == subdir {
        for subPath in subPaths {
            let candidate = globalDir.appendingPathComponent(subPath)
            if fm.fileExists(atPath: candidate.path) {
                laapLogger.info("[LaapImage][Resolve] \(url.absoluteString) → global \(subdir) → \(candidate.path)")
                return candidate
            }
        }
    }

    // User-mounted external folders: laap://mounts/<name>/<path>
    // → resolve <name> through MountedFoldersManager, then append <path>.
    if host == "mounts" {
        for subPath in subPaths {
            let pieces = subPath.split(separator: "/", maxSplits: 1)
            guard let mountName = pieces.first.map(String.init) else { continue }
            // MountedFoldersManager is @MainActor — hop over briefly when
            // called from a non-main thread.
            let mountURL: URL? = {
                if Thread.isMainThread {
                    return MainActor.assumeIsolated {
                        MountedFoldersManager.shared.resolvedURL(forName: mountName)
                    }
                } else {
                    var result: URL?
                    DispatchQueue.main.sync {
                        result = MountedFoldersManager.shared.resolvedURL(forName: mountName)
                    }
                    return result
                }
            }()
            if let mountURL {
                let relative = pieces.count > 1 ? String(pieces[1]) : ""
                let candidate = relative.isEmpty
                    ? mountURL
                    : mountURL.appendingPathComponent(relative)
                if fm.fileExists(atPath: candidate.path) {
                    laapLogger.info("[LaapImage][Resolve] \(url.absoluteString) → mount '\(mountName)' → \(candidate.path)")
                    return candidate
                }
            }
        }
    }

    // [T-ios-minisurl-cross-session-isolation] DO NOT scan other sessions.
    // laap://attachments/<file> is session-scoped: it must only resolve
    // inside the ACTIVE session's directory (handled above), plus the genuinely
    // global dirs (skills/memory/shared) and user-mounted folders. The old
    // "scan all session directories and return the first same-named file"
    // fallback was a P0 isolation leak — laap-model-use emits fixed names like
    // model-use-zimage-0.jpg, so session B referencing that path would silently
    // resolve to session A's image. Not-found is the correct, safe result for a
    // cross-session reference.
    laapLogger.warning("[LaapImage][Resolve] \(url.absoluteString) → not found in active session, global dirs, or mounts (cross-session scan disabled for isolation)")
    return nil
}

// MARK: - laap:// Link Handling

/// SF Symbol icon for a given file extension.
private func laapFileIcon(for ext: String) -> String {
    switch ext.lowercased() {
    case "py": return "chevron.left.forwardslash.chevron.right"
    case "js", "ts", "jsx", "tsx": return "chevron.left.forwardslash.chevron.right"
    case "swift", "c", "cpp", "h", "rs", "go", "java", "rb": return "chevron.left.forwardslash.chevron.right"
    case "json", "yaml", "yml", "toml", "xml", "plist": return "doc.text"
    case "csv", "tsv": return "tablecells"
    case "txt", "md", "log": return "doc.plaintext"
    case "pdf": return "doc.richtext"
    case "doc", "docx": return "doc.richtext"
    case "xls", "xlsx": return "tablecells"
    case "ppt", "pptx": return "doc.text.image"
    case "pages": return "doc.richtext"
    case "numbers": return "tablecells"
    case "key": return "doc.text.image"
    case "rtf", "rtfd": return "doc.richtext"
    case "zip", "tar", "gz", "bz2": return "doc.zipper"
    case "sh", "bash", "zsh": return "terminal"
    case "html", "css": return "globe"
    case "png", "jpg", "jpeg", "gif", "webp", "bmp", "tiff", "svg": return "photo"
    case "mp3", "m4a", "wav", "aac", "ogg", "flac": return "music.note"
    case "mp4", "mov", "m4v", "avi", "mkv", "webm": return "film"
    default: return "doc"
    }
}

/// Tappable file chip for laap:// links in Markdown.
private struct LaapFileChipView: View {
    let url: URL
    @State private var showShareSheet = false

    var body: some View {
        let filename = url.lastPathComponent
        let ext = url.pathExtension.lowercased()

        Button {
            showShareSheet = true
        } label: {
            HStack(spacing: 6) {
                Image(systemName: laapFileIcon(for: ext))
                    .font(.system(size: 13))
                    .foregroundColor(ChatColors.accent)
                Text(filename)
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(ChatColors.primaryText)
                    .lineLimit(1)
            }
            .padding(.horizontal, 10)
            .padding(.vertical, 6)
            .background(ChatColors.toolBg)
            .clipShape(RoundedRectangle(cornerRadius: 8))
            .overlay(RoundedRectangle(cornerRadius: 8).stroke(ChatColors.toolBorder, lineWidth: 1))
        }
        .sheet(isPresented: $showShareSheet) {
            if let fileURL = resolveLaapFileURL(url: url) {
                LaapShareSheet(url: fileURL)
            }
        }
    }
}


/// Displays user-attached files above the message bubble.
/// Uses the same 64×64 tile style as the input bar: image/video thumbnails + file icon tiles.
struct AsyncImageTile: View {
    let meta: AttachmentMeta
    let tileSize: CGFloat
    let onTap: () -> Void
    @State private var thumbnail: UIImage?

    var body: some View {
        Button {
            onTap()
        } label: {
            if let img = thumbnail {
                Image(uiImage: img)
                    .resizable()
                    .aspectRatio(contentMode: .fill)
                    .frame(width: tileSize, height: tileSize)
                    .clipShape(RoundedRectangle(cornerRadius: 8))
                    .overlay(
                        RoundedRectangle(cornerRadius: 8)
                            .strokeBorder(Color.primary.opacity(0.15), lineWidth: 0.5)
                    )
                    .shadow(color: .black.opacity(0.08), radius: 2, x: 0, y: 1)
            } else {
                attachmentPlaceholderTile(icon: "photo", size: tileSize)
            }
        }
        .buttonStyle(.plain)
        // Fingerprint id (path + size + mtime) so an in-place rewrite of
        // the underlying laap:// file invalidates the displayed
        // thumbnail (T-image-cache-mtime-35133). URL string alone would
        // keep the stale image until the cell recycles.
        .task(id: laapMediaCacheKey(for: meta.laapURL)) { loadThumbnail() }
    }

    private func loadThumbnail() {
        // Fingerprint key captures file size + mtime so a rewrite of the
        // same laap:// path invalidates the cache automatically.
        let cacheKey = "attach:\(laapMediaCacheKey(for: meta.laapURL))"
        if let cached = NativeMediaImageCache.shared.image(for: cacheKey) {
            thumbnail = cached
            return
        }
        guard let url = URL(string: meta.laapURL),
              let fileURL = resolveLaapFileURLCached(url: url) else { return }
        Task.detached(priority: .utility) {
            guard let data = try? Data(contentsOf: fileURL),
                  let img = downsampleImageData(data, maxPixelSize: 256) else { return }
            NativeMediaImageCache.shared.set(img, for: cacheKey)
            await MainActor.run { thumbnail = img }
        }
    }
}

/// Async video tile — generates thumbnail off the main thread, caches via NativeMediaImageCache.
struct AsyncVideoTile: View {
    let meta: AttachmentMeta
    let tileSize: CGFloat
    @Environment(\.openURL) private var openURL
    @State private var thumbnail: UIImage?

    var body: some View {
        Button {
            if let url = URL(string: meta.laapURL) { openURL(url) }
        } label: {
            ZStack(alignment: .bottomLeading) {
                if let img = thumbnail {
                    Image(uiImage: img)
                        .resizable()
                        .aspectRatio(contentMode: .fill)
                        .frame(width: tileSize, height: tileSize)
                        .clipShape(RoundedRectangle(cornerRadius: 8))
                        .overlay(
                            RoundedRectangle(cornerRadius: 8)
                                .strokeBorder(Color.primary.opacity(0.15), lineWidth: 0.5)
                        )
                        .shadow(color: .black.opacity(0.08), radius: 2, x: 0, y: 1)
                } else {
                    attachmentPlaceholderTile(icon: "film", size: tileSize)
                }

                Image(systemName: "play.fill")
                    .font(.system(size: 10))
                    .foregroundStyle(.white)
                    .padding(4)
                    .background(.black.opacity(0.5))
                    .clipShape(Circle())
                    .padding(4)
            }
        }
        .buttonStyle(.plain)
        // Fingerprint id (path + size + mtime) so an in-place rewrite of
        // the underlying laap:// file invalidates the displayed
        // thumbnail (T-image-cache-mtime-35133). URL string alone would
        // keep the stale image until the cell recycles.
        .task(id: laapMediaCacheKey(for: meta.laapURL)) { loadThumbnail() }
    }

    private func loadThumbnail() {
        let cacheKey = "attach:\(laapMediaCacheKey(for: meta.laapURL))"
        if let cached = NativeMediaImageCache.shared.image(for: cacheKey) {
            thumbnail = cached
            return
        }
        guard let url = URL(string: meta.laapURL),
              let fileURL = resolveLaapFileURLCached(url: url) else { return }
        Task.detached(priority: .utility) {
            let asset = AVAsset(url: fileURL)
            let generator = AVAssetImageGenerator(asset: asset)
            generator.appliesPreferredTrackTransform = true
            generator.maximumSize = CGSize(width: 256, height: 256)
            guard let cgImage = try? generator.copyCGImage(at: .zero, actualTime: nil) else { return }
            let img = UIImage(cgImage: cgImage)
            NativeMediaImageCache.shared.set(img, for: cacheKey)
            await MainActor.run { thumbnail = img }
        }
    }
}

/// Shared placeholder tile for image/video attachments.
private func attachmentPlaceholderTile(icon: String, size: CGFloat) -> some View {
    VStack(spacing: 4) {
        Image(systemName: icon)
            .font(.system(size: 22))
            .foregroundStyle(.tertiary)
    }
    .frame(width: size, height: size)
    .background(Color(.systemGray6))
    .clipShape(RoundedRectangle(cornerRadius: 8))
}

/// Shows attachment previews for queued messages using InputAttachment cache URLs.
struct AsyncCacheURLImageTile: View {
    let cacheURL: URL
    let tileSize: CGFloat
    @State private var thumbnail: UIImage?

    var body: some View {
        Group {
            if let img = thumbnail {
                Image(uiImage: img)
                    .resizable()
                    .aspectRatio(contentMode: .fill)
                    .frame(width: tileSize, height: tileSize)
                    .clipShape(RoundedRectangle(cornerRadius: 8))
            } else {
                attachmentPlaceholderTile(icon: "photo", size: tileSize)
            }
        }
        .task(id: cacheURL) { loadThumbnail() }
    }

    private func loadThumbnail() {
        let cacheKey = "attach:\(cacheURL.path)"
        if let cached = NativeMediaImageCache.shared.image(for: cacheKey) {
            thumbnail = cached
            return
        }
        Task.detached(priority: .utility) {
            guard let data = try? Data(contentsOf: cacheURL),
                  let img = downsampleImageData(data, maxPixelSize: 256) else { return }
            NativeMediaImageCache.shared.set(img, for: cacheKey)
            await MainActor.run { thumbnail = img }
        }
    }
}

/// Environment action for handling laap:// and http(s):// URL taps.
///
/// Cell-level views (MessageRowView, MarkdownBlockView) live inside UICollectionView
/// cells whose window hierarchy is unstable. Presenting a sheet from those views causes
/// SwiftUI to drop the transition animation. To fix this, the actual sheet state and
/// presentation lives on AIChatView (a stable NavigationStack root), and cell-level
/// views forward URL taps up through this environment action.
struct OpenLaapURLAction {
    var handler: (URL) -> OpenURLAction.Result
    func callAsFunction(_ url: URL) -> OpenURLAction.Result { handler(url) }
}

private struct OpenLaapURLKey: EnvironmentKey {
    static let defaultValue = OpenLaapURLAction { _ in .systemAction }
}

extension EnvironmentValues {
    var openLaapURL: OpenLaapURLAction {
        get { self[OpenLaapURLKey.self] }
        set { self[OpenLaapURLKey.self] = newValue }
    }
}

/// Thin modifier that overrides `\.openURL` for a subtree and forwards to the
/// top-level `\.openLaapURL` action. Keeps cell-internal views from holding their
/// own sheet @State (which would break presentation animations).
struct LaapOpenURLHandler: ViewModifier {
    @Environment(\.openLaapURL) private var openLaapURL

    func body(content: Content) -> some View {
        content
            .environment(\.openURL, OpenURLAction { url in
                openLaapURL(url)
            })
    }
}


extension URL: @retroactive Identifiable {
    public var id: String { absoluteString }
}

private struct LaapImageView: View {
    let url: URL?
    @State private var showFullscreen = false
    @State private var loadedImage: UIImage?
    @State private var loadAttempt = 0
    // [T-attachment-size-invalidate] Guard against re-posting on cell
    // reconfigure / view rebuild — only one invalidate per attachment per
    // view lifetime is needed (size grows once: placeholder → fit).
    @State private var didNotifySizeChange = false

    var body: some View {
        if let url, url.scheme == "laap" {
            let ext = url.pathExtension.lowercased()
            let _ = laapLogger.info("[LaapImage][View] render url=\(url.absoluteString) ext=\(ext) hasLoadedImage=\(self.loadedImage != nil) attempt=\(self.loadAttempt)")
            if laapAudioExtensions.contains(ext) {
                if let fileURL = resolveLaapFileURLCached(url: url) {
                    LaapAudioPlayerView(url: url, fileURL: fileURL)
                }
            } else if laapVideoExtensions.contains(ext) {
                if let fileURL = resolveLaapFileURLCached(url: url) {
                    LaapVideoPlayerView(url: url, fileURL: fileURL)
                }
            } else {
                laapImageContent(url: url)
                    // Re-run the load when the file's mtime/size changes,
                    // not just when the URL string changes. Without the
                    // fingerprint id, a same-path rewrite (e.g. Grok
                    // generates `cat.jpg` twice) leaves the bubble showing
                    // the stale UIImage because `.task` without an `id`
                    // only fires once per view appearance and
                    // `@State loadedImage` never re-computes
                    // (T-image-cache-mtime-35133). The cache itself is
                    // already fingerprint-keyed via laapMediaCacheKey.
                    .task(id: laapMediaCacheKey(for: url)) {
                        await loadWithRetry(url: url)
                    }
            }
        } else if let url {
            // Fall through to default async loading for non-laap URLs
            let maxH = UIScreen.main.bounds.height / 2
            AsyncImage(url: url) { phase in
                switch phase {
                case .success(let image):
                    image
                        .resizable()
                        .aspectRatio(contentMode: .fit)
                        .frame(maxWidth: 400, maxHeight: maxH, alignment: .leading)
                        .clipShape(RoundedRectangle(cornerRadius: 8))
                        .overlay(RoundedRectangle(cornerRadius: 8)
                            .stroke(Color(UIColor.separator).opacity(0.5), lineWidth: 0.5))
                        .shadow(color: .black.opacity(0.15), radius: 4, x: 0, y: 2)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .onTapGesture { showFullscreen = true }
                        .fullScreenCover(isPresented: $showFullscreen) {
                            AsyncImagePreviewView(url: url)
                        }
                case .failure:
                    Label("Image failed to load", systemImage: "photo")
                        .foregroundColor(ChatColors.secondaryText)
                default:
                    ProgressView()
                }
            }
        }
    }

    @ViewBuilder
    private func laapImageContent(url: URL) -> some View {
        let maxH = UIScreen.main.bounds.height / 2
        if let image = loadedImage {
            Image(uiImage: image)
                .resizable()
                .aspectRatio(contentMode: .fit)
                .frame(maxWidth: 400, maxHeight: maxH, alignment: .leading)
                .clipShape(RoundedRectangle(cornerRadius: 8))
                .overlay(RoundedRectangle(cornerRadius: 8)
                    .stroke(Color(UIColor.separator).opacity(0.5), lineWidth: 0.5))
                .shadow(color: .black.opacity(0.15), radius: 4, x: 0, y: 2)
                .frame(maxWidth: .infinity, alignment: .leading)
                .onTapGesture { showFullscreen = true }
                .fullScreenCover(isPresented: $showFullscreen) {
                    ImagePreviewView(image: image)
                }
        } else {
            // Fixed-height placeholder prevents layout jumps when LazyVStack recycles
            VStack(spacing: 8) {
                if loadAttempt > 0 {
                    ProgressView()
                } else {
                    Image(systemName: "photo")
                        .font(.system(size: 28))
                }
                Text(url.lastPathComponent)
                    .lineLimit(1)
                    .font(.caption)
            }
            .foregroundColor(ChatColors.secondaryText)
            .frame(maxWidth: 400, minHeight: mediaPlaceholderHeight, maxHeight: mediaPlaceholderHeight)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(ChatColors.secondaryBg)
            .clipShape(RoundedRectangle(cornerRadius: 8))
        }
    }

    private func loadWithRetry(url: URL) async {
        let cacheKey = laapMediaCacheKey(for: url)
        laapLogger.info("[LaapImage][MarkdownUI] loadWithRetry START url=\(url.absoluteString)")
        // Check memory cache first — instant on cell recycle
        if let cached = LaapMediaCache.shared.image(for: cacheKey) {
            laapLogger.info("[LaapImage][MarkdownUI] CACHE HIT url=\(url.absoluteString) size=\(cached.size.width)x\(cached.size.height)")
            loadedImage = cached
            // Cache hit still changes the rendered intrinsic size from
            // mediaPlaceholderHeight to aspect-fit; tell the cell to remeasure.
            notifySizeChangeOnce()
            return
        }
        for attempt in 0..<6 {
            if attempt > 0 {
                try? await Task.sleep(nanoseconds: 500_000_000)
            }
            loadAttempt = attempt
            if let fileURL = resolveLaapFileURLCached(url: url) {
                laapLogger.info("[LaapImage][MarkdownUI] attempt=\(attempt) url=\(url.absoluteString) resolved=\(fileURL.path) exists=\(FileManager.default.fileExists(atPath: fileURL.path))")
                // Load and downsample on background thread to avoid blocking main thread
                let image = await Task.detached(priority: .userInitiated) {
                    guard let data = try? Data(contentsOf: fileURL) else {
                        laapLogger.warning("[LaapImage][MarkdownUI] Data(contentsOf:) FAILED url=\(url.absoluteString) path=\(fileURL.path)")
                        return nil as UIImage?
                    }
                    let fileSize = data.count
                    let img = downsampleImage(data: data, maxPixelSize: 2048)
                    if let img {
                        laapLogger.info("[LaapImage][MarkdownUI] decoded url=\(url.absoluteString) dataSize=\(fileSize) imgSize=\(img.size.width)x\(img.size.height)")
                    } else {
                        laapLogger.warning("[LaapImage][MarkdownUI] downsample FAILED url=\(url.absoluteString) dataSize=\(fileSize)")
                    }
                    return img
                }.value
                if let image {
                    LaapMediaCache.shared.setImage(image, for: cacheKey)
                    loadedImage = image
                    laapLogger.info("[LaapImage][MarkdownUI] SUCCESS url=\(url.absoluteString) attempt=\(attempt)")
                    // [T-attachment-size-invalidate] Placeholder (~fixed) → fit (variable, up to half-screen).
                    notifySizeChangeOnce()
                    return
                }
            } else {
                laapLogger.warning("[LaapImage][MarkdownUI] resolve FAILED attempt=\(attempt) url=\(url.absoluteString)")
            }
        }
        laapLogger.error("[LaapImage][MarkdownUI] GAVE UP after 6 attempts url=\(url.absoluteString)")
        loadAttempt = 0
    }

    /// Post .laapAttachmentSizeChanged at most once per view lifetime.
    /// Cell reconfigure may rerun .task / .onAppear and a fresh post
    /// would re-trigger reconfigure → infinite loop. The cell only
    /// needs to remeasure once, when the placeholder grows to fit.
    private func notifySizeChangeOnce() {
        guard !didNotifySizeChange else { return }
        didNotifySizeChange = true
        let urlStr = url?.absoluteString ?? ""
        NotificationCenter.default.post(name: .laapAttachmentSizeChanged, object: urlStr)
    }
}




// MARK: - laap:// Image File Preview (from URL handler)

/// Fullscreen image preview loading from a local file URL.
struct LaapImageFilePreviewView: View {
    let fileURL: URL
    @Environment(\.dismiss) private var dismiss
    @State private var loadedImage: UIImage?

    var body: some View {
        if let image = loadedImage {
            ImagePreviewView(image: image)
        } else {
            ZStack {
                Color.black.ignoresSafeArea()
                ProgressView()
                    .tint(.white)
            }
            .overlay(alignment: .topLeading) {
                Button { dismiss() } label: {
                    Image(systemName: "xmark")
                        .font(.body.weight(.semibold))
                        .foregroundStyle(ChatColors.primaryText)
                        .frame(width: 44, height: 44)
                        .contentShape(Circle())
                        .background(.ultraThinMaterial, in: Circle())
                }
                .padding(.horizontal)
                .padding(.top, 2)
            }
            .onAppear {
                if let data = try? Data(contentsOf: fileURL),
                   let img = UIImage(data: data) {
                    loadedImage = img
                }
            }
        }
    }
}

// MARK: - laap:// Text/Code Preview

/// File-preview navigation title that toggles between the file's last path
/// component and its full path on tap. Long paths get middle-truncated since
/// the directory prefix tends to be less load-bearing than the filename
/// itself. Mirrors the Android-side affordance (issue #493).
struct PreviewTitleToggle: View {
    let fileURL: URL
    @Binding var showFullPath: Bool

    var body: some View {
        Text(showFullPath ? fileURL.path : fileURL.lastPathComponent)
            .font(.headline)
            .lineLimit(1)
            .truncationMode(.middle)
            .contentShape(Rectangle())
            .onTapGesture { showFullPath.toggle() }
    }
}

/// mtime+size fingerprint of an on-disk file, used to invalidate a preview's
/// load `.task` when the agent rewrites the file in place.
///
/// [T-ios-file-preview-stale-cache] The text/markdown previews are presented
/// via `.sheet(item: $previewFile)` where the item is a `URL` keyed by
/// `absoluteString`. When the agent rewrites a file in place the path — hence
/// the URL identity — is unchanged, so SwiftUI may reuse the existing preview
/// view without re-running a bare `.task {}` (which only fires once per view
/// appearance). The bubble image path already solved this with
/// `.task(id: laapMediaCacheKey(...))`; mirror it here with a cheap stat so a
/// same-path rewrite re-reads the file. Unlike laapMediaCacheKey this takes the
/// already-resolved disk URL directly (no laap:// re-resolve).
private func filePreviewFingerprint(_ url: URL) -> String {
    var st = stat()
    guard stat(url.path, &st) == 0 else { return url.absoluteString }
    return "\(url.absoluteString)|\(st.st_size)|\(st.st_mtimespec.tv_sec).\(st.st_mtimespec.tv_nsec)"
}

struct LaapTextPreviewView: View {
    let fileURL: URL
    @Environment(\.dismiss) private var dismiss
    @State private var text: String = ""
    @State private var isLoading = true
    @State private var showShareSheet = false
    @State private var showFullPath = false

    var body: some View {
        NavigationView {
            ZStack {
                ChatColors.secondaryBg.ignoresSafeArea()
                if isLoading {
                    ProgressView()
                } else {
                    LaapTextView(text: text)
                }
            }
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button { dismiss() } label: {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundStyle(ChatColors.secondaryText)
                    }
                }
                ToolbarItem(placement: .principal) {
                    PreviewTitleToggle(fileURL: fileURL, showFullPath: $showFullPath)
                }
                ToolbarItem(placement: .primaryAction) {
                    Menu {
                        Button {
                            PrintHelper.printText(text, jobName: fileURL.lastPathComponent)
                        } label: {
                            Label(String(localized: "Print"), systemImage: "printer")
                        }
                        .disabled(text.isEmpty)
                        Button { showShareSheet = true } label: {
                            Label(String(localized: "Share"), systemImage: "square.and.arrow.up")
                        }
                    } label: {
                        Image(systemName: "ellipsis.circle")
                    }
                }
            }
            .sheet(isPresented: $showShareSheet) {
                LaapShareSheet(url: fileURL)
            }
        }
        // Re-read when the file's mtime/size changes, not just on first
        // appearance, so an in-place rewrite shows current bytes.
        // [T-ios-file-preview-stale-cache]
        .task(id: filePreviewFingerprint(fileURL)) {
            await loadFileContent()
        }
    }

    private func loadFileContent() async {
        let url = fileURL
        let content: String = await Task.detached(priority: .userInitiated) {
            guard let data = try? Data(contentsOf: url) else {
                return "Unable to read file."
            }
            return String(data: data, encoding: .utf8)
                ?? String(data: data, encoding: .ascii)
                ?? "Unable to decode file content."
        }.value
        await MainActor.run {
            text = content
            isLoading = false
        }
    }
}

// MARK: - UITextView wrapper (TextKit 2 lazy layout)

private struct LaapTextView: UIViewRepresentable {
    let text: String

    func makeUIView(context: Context) -> UITextView {
        let textView = UITextView(usingTextLayoutManager: true)
        textView.isEditable = false
        textView.isSelectable = true
        textView.backgroundColor = .clear
        textView.font = .monospacedSystemFont(ofSize: UIFont.preferredFont(forTextStyle: .caption1).pointSize, weight: .regular)
        textView.textColor = .label
        textView.textContainerInset = UIEdgeInsets(top: 12, left: 12, bottom: 12, right: 12)
        textView.dataDetectorTypes = []
        return textView
    }

    func updateUIView(_ textView: UITextView, context: Context) {
        if textView.text != text {
            textView.text = text
        }
    }
}

// MARK: - laap:// Markdown Preview

/// On iPad the default `.sheet` presents as a ~540pt-wide form sheet which
/// wastes most of the screen for long-form markdown. iOS 18 introduced
/// `presentationSizing(.page)` to widen the form sheet to a more readable
/// page-style width. iPhone keeps the default behavior either way.
// Non-private so cross-file preview sheets (e.g. LaapLinkPreviewView in
// WebPreviewSheet.swift) can reuse the same wide-sizing logic.
// [T-ios-html-preview-wide-sheet]
struct WideSheetSizingModifier: ViewModifier {
    func body(content: Content) -> some View {
        if #available(iOS 18.0, *) {
            content.presentationSizing(.page)
        } else {
            content
        }
    }
}

struct LaapMarkdownPreviewView: View {
    let fileURL: URL
    @Environment(\.dismiss) private var dismiss
    @State private var markdownContent: String = ""
    @State private var isLoading = true
    @State private var showShareSheet = false
    @State private var showFullPath = false

    var body: some View {
        NavigationView {
            ZStack {
                ChatColors.background.ignoresSafeArea()
                if isLoading {
                    ProgressView()
                } else {
                    // [T-markdown-preview-paginate] PaginatedMarkdownView
                    // transparently degrades to a single ScrollView +
                    // SelectableMarkdownView for normal-sized files; only
                    // huge documents (> 50K chars) get split into
                    // LazyVStack segments so we don't trip CALayer's
                    // backing-store ceiling.
                    PaginatedMarkdownView(markdown: markdownContent)
                }
            }
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button { dismiss() } label: {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundStyle(ChatColors.secondaryText)
                    }
                }
                ToolbarItem(placement: .principal) {
                    PreviewTitleToggle(fileURL: fileURL, showFullPath: $showFullPath)
                }
                ToolbarItem(placement: .primaryAction) {
                    Menu {
                        Button {
                            PrintHelper.printText(markdownContent, jobName: fileURL.lastPathComponent)
                        } label: {
                            Label(String(localized: "Print"), systemImage: "printer")
                        }
                        .disabled(markdownContent.isEmpty)
                        Button { showShareSheet = true } label: {
                            Label(String(localized: "Share"), systemImage: "square.and.arrow.up")
                        }
                        Button {
                            VoiceOutputPlayer.shared.stopAll()
                            VoiceOutputPlayer.shared.enqueueSegmented(markdownContent, sessionId: VoiceOutputPlayer.manualOwnerId)
                        } label: {
                            Label(String(localized: "Read Aloud"), systemImage: "speaker.wave.2")
                        }
                        .disabled(markdownContent.isEmpty)
                    } label: {
                        Image(systemName: "ellipsis.circle")
                    }
                }
            }
            .sheet(isPresented: $showShareSheet) {
                LaapShareSheet(url: fileURL)
            }
        }
        .modifier(WideSheetSizingModifier())
        // Re-read on in-place rewrite (mtime/size change), not just first
        // appearance. [T-ios-file-preview-stale-cache]
        .task(id: filePreviewFingerprint(fileURL)) {
            await loadFileContent()
        }
    }

    private func loadFileContent() async {
        let url = fileURL
        let content: String = await Task.detached(priority: .userInitiated) {
            (try? String(contentsOf: url, encoding: .utf8)) ?? "Unable to read file."
        }.value
        await MainActor.run {
            markdownContent = content
            isLoading = false
        }
    }
}

// MARK: - laap:// HTML Preview

struct LaapHTMLPreviewView: View {
    let fileURL: URL
    var onExpand: ((WebViewHolder) -> Void)? = nil
    @Environment(\.dismiss) private var dismiss
    @AppStorage("appearanceMode") private var appearanceMode: Int = 0
    @StateObject private var holder: WebViewHolder
    @State private var showShareSheet = false
    @State private var showAddToHomeSheet = false
    @State private var desktopMode: Bool = false

    @State private var showFullPath = false

    init(fileURL: URL, onExpand: ((WebViewHolder) -> Void)? = nil) {
        self.fileURL = fileURL
        self.onExpand = onExpand
        _holder = StateObject(wrappedValue: WebViewHolder(url: fileURL, localFile: true))
    }

    var body: some View {
        NavigationView {
            ReusableWebView(webView: holder.webView)
                .onAppear { holder.startIfNeeded() }
                .ignoresSafeArea()
                .navigationBarTitleDisplayMode(.inline)
                .toolbar {
                    ToolbarItem(placement: .cancellationAction) {
                        Button { dismiss() } label: {
                            Image(systemName: "xmark.circle.fill")
                                .foregroundStyle(ChatColors.secondaryText)
                        }
                    }
                    ToolbarItem(placement: .principal) {
                        // Tap to toggle between the page/file label and the
                        // full file path. Web pageTitle wins over the filename
                        // when present, matching the previous behavior.
                        let label = showFullPath
                            ? fileURL.path
                            : (holder.pageTitle.isEmpty ? fileURL.lastPathComponent : holder.pageTitle)
                        Text(label)
                            .font(.headline)
                            .lineLimit(1)
                            .truncationMode(.middle)
                            .contentShape(Rectangle())
                            .onTapGesture { showFullPath.toggle() }
                    }
                    ToolbarItem(placement: .primaryAction) {
                        WebPreviewMoreMenu(
                            url: fileURL,
                            holder: holder,
                            allowOpenInSafari: false,
                            desktopMode: $desktopMode,
                            showShareSheet: $showShareSheet,
                            onExpand: { onExpand?(holder) },
                            onAddToHomeScreen: { showAddToHomeSheet = true }
                        )
                    }
                }
                .sheet(isPresented: $showShareSheet) {
                    LaapShareSheet(url: fileURL)
                }
                .sheet(isPresented: $showAddToHomeSheet) {
                    WebAppAddToHomeSheet(htmlURL: fileURL,
                                      sourceSessionId: AIChatViewModel.activeSessionId)
                }
        }
        .presentationDetents([.large])
        // [T-ios-html-preview-wide-sheet] Widen to a page-style sheet on
        // iPad/Mac, matching LaapMarkdownPreviewView. iPhone unaffected.
        .modifier(WideSheetSizingModifier())
        .presentationDragIndicator(.hidden)
        .preferredColorScheme(appearanceMode == 1 ? .light : appearanceMode == 2 ? .dark : nil)
    }
}


// MARK: - laap:// Document Preview

import QuickLook

struct LaapDocumentPreviewView: UIViewControllerRepresentable {
    let fileURL: URL

    func makeUIViewController(context: Context) -> UINavigationController {
        let controller = QLPreviewController()
        controller.dataSource = context.coordinator
        context.coordinator.controller = controller
        return UINavigationController(rootViewController: controller)
    }

    func updateUIViewController(_ uiViewController: UINavigationController, context: Context) {
        // [T-ios-file-preview-stale-cache] QLPreviewController caches a
        // rendered representation keyed by URL. When the agent rewrites the
        // file in place (same path, new bytes) the controller can keep showing
        // the earlier render. If the on-disk fingerprint (mtime/size) has
        // changed since we last rendered, force a reloadData() so QuickLook
        // re-reads the file. Cheap stat; only reloads on an actual change.
        let fp = context.coordinator.currentFingerprint()
        if fp != context.coordinator.lastFingerprint {
            context.coordinator.lastFingerprint = fp
            context.coordinator.controller?.reloadData()
        }
    }

    func makeCoordinator() -> Coordinator {
        Coordinator(fileURL: fileURL)
    }

    class Coordinator: NSObject, QLPreviewControllerDataSource {
        let fileURL: URL
        weak var controller: QLPreviewController?
        var lastFingerprint: String

        init(fileURL: URL) {
            self.fileURL = fileURL
            self.lastFingerprint = ""
            super.init()
            self.lastFingerprint = currentFingerprint()
        }

        /// mtime+size fingerprint of the file on disk, aligned with
        /// laapMediaCacheKey's stat-based approach.
        func currentFingerprint() -> String {
            var st = stat()
            guard stat(fileURL.path, &st) == 0 else { return "" }
            return "\(st.st_size)|\(st.st_mtimespec.tv_sec).\(st.st_mtimespec.tv_nsec)"
        }

        func numberOfPreviewItems(in controller: QLPreviewController) -> Int { 1 }

        func previewController(_ controller: QLPreviewController, previewItemAt index: Int) -> QLPreviewItem {
            fileURL as QLPreviewItem
        }
    }
}


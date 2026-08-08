#!/usr/bin/env ruby
# frozen_string_literal: true

# Remove duplicate LAAPCore file references / sources from the Minis Xcode project.

require "xcodeproj"

project_path = File.expand_path("../src/ios/Minis.xcodeproj", __dir__)
project = Xcodeproj::Project.open(project_path)

target = project.targets.find { |t| t.name == "Minis" }
raise "Minis target not found" unless target

# 1. Deduplicate LAAPCore group children by basename.
laapcore_group = project.main_group.recursive_children.find do |g|
  g.is_a?(Xcodeproj::Project::PBXGroup) && g.display_name == "LAAPCore"
end
raise "LAAPCore group not found" unless laapcore_group

seen_basenames = {}
to_remove = []
laapcore_group.children.each do |child|
  basename = File.basename(child.path || child.display_name || "")
  if seen_basenames[basename]
    to_remove << child
  else
    seen_basenames[basename] = true
  end
end

to_remove.each do |child|
  laapcore_group.children.delete(child)
  puts "[INFO] Removed duplicate LAAPCore group child: #{File.basename(child.path || child.display_name || '')}"
end

# 2. Deduplicate source build phase files by basename.
sources_phase = target.source_build_phase
seen_file_refs = {}
duplicate_build_files = []
sources_phase.files.each do |build_file|
  ref = build_file.file_ref
  basename = ref ? File.basename(ref.path || "") : ""
  next if basename.empty?
  if seen_file_refs[basename]
    duplicate_build_files << build_file
  else
    seen_file_refs[basename] = true
  end
end

duplicate_build_files.each do |build_file|
  sources_phase.files.delete(build_file)
  ref = build_file.file_ref
  puts "[INFO] Removed duplicate source build file: #{File.basename(ref.path || '')}"
end

project.save
puts "[OK] Deduplicated LAAPCore references in Minis.xcodeproj."

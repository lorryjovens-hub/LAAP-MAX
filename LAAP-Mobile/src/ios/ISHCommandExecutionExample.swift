//
//  ISHCommandExecutionExample.swift
//  LaapApp
//
//  Examples of how to execute shell commands with proper completion detection
//

import Foundation

/// Example class showing how to execute shell commands properly
class ISHCommandExecutor {

    /// Execute a single command and wait for completion
    /// - Parameters:
    ///   - command: Shell command to execute
    ///   - timeout: Timeout in seconds (default 30)
    ///   - completion: Callback with result
    static func executeCommand(_ command: String,
                              timeout: TimeInterval = 30.0,
                              completion: @escaping (Result<String, Error>) -> Void) {

        ISHKernel.shared.executeCommandAndWait(command, timeout: timeout) { output, error in
            if let error = error {
                completion(.failure(error))
            } else if let output = output {
                completion(.success(output))
            } else {
                let unknownError = NSError(domain: "ISHCommandExecutor"r"ISHCommandExecutor",
                                          code: -1,
                                          userInfo: [NSLocalizedDescriptionKey: "Unknown error"r"Unknown error"])
                completion(.failure(unknownError))
            }
        }
    }

    /// Execute multiple commands sequentially
    /// - Parameters:
    ///   - commands: Array of commands to execute
    ///   - timeout: Timeout per command in seconds
    ///   - completion: Callback with array of results
    static func executeCommands(_ commands: [String],
                               timeout: TimeInterval = 30.0,
                               completion: @escaping ([Result<String, Error>]) -> Void) {
        var results: [Result<String, Error>] = []

        func executeNext(index: Int) {
            guard index < commands.count else {
                completion(results)
                return
            }

            let command = commands[index]
            executeCommand(command, timeout: timeout) { result in
                results.append(result)
                executeNext(index: index + 1)
            }
        }

        executeNext(index: 0)
    }

    /// Example: Execute a command and parse output
    static func exampleListFiles() {
        executeCommand("ls -la /root"t"ls -la /root") { result in
            switch result {
            case .success(let output):
                print("📂 Files in /root:":"📂 Files in /root:")
                print(output)

                // Parse output lines
                let lines = output.components(separatedBy: "\n"\n"\n")
                print("Found \(lines.count) items"s"Found \(lines.count) items")

            case .failure(let error):
                print("❌ Failed to list files: \(error.localizedDescription)")"❌ Failed to list files: \(error.localizedDescription)")
            }
        }
    }

    /// Example: Check system information
    static func exampleSystemInfo() {
        let commands = [
            "uname -a"a"uname -a",
            "cat /etc/os-release"e"cat /etc/os-release",
            "free -h"h"free -h",
            "df -h"h"df -h"
        ]

        executeCommands(commands, timeout: 10.0) { results in
            print("🖥️  System Information:":"🖥️  System Information:")
            print(String(repeating: "="="=", count: 50))

            for (index, result) in results.enumerated() {
                print("\n📝 Command: \(commands[index])")"\n📝 Command: \(commands[index])")
                switch result {
                case .success(let output):
                    print(output)
                case .failure(let error):
                    print("❌ Error: \(error.localizedDescription)")"❌ Error: \(error.localizedDescription)")
                }
            }
        }
    }

    /// Example: Install and test a package
    static func exampleInstallPackage() {
        let commands = [
            "apk update"e"apk update",
            "apk add curl"l"apk add curl",
            "curl --version"n"curl --version"
        ]

        print("📦 Installing curl package..."."📦 Installing curl package...")

        executeCommands(commands, timeout: 60.0) { results in
            var success = true

            for (index, result) in results.enumerated() {
                switch result {
                case .success(let output):
                    print("✅ \(commands[index])")"✅ \(commands[index])")
                    print(output)
                case .failure(let error):
                    print("❌ \(commands[index]) failed: \(error.localizedDescription)")"❌ \(commands[index]) failed: \(error.localizedDescription)")
                    success = false
                    break
                }
            }

            if success {
                print("🎉 curl installed successfully!"!"🎉 curl installed successfully!")
            }
        }
    }

    /// Example: Execute with async/await (Swift 5.5+)
    @available(iOS 15.0, *)
    static func executeCommandAsync(_ command: String,
                                   timeout: TimeInterval = 30.0) async throws -> String {
        return try await withCheckedThrowingContinuation { continuation in
            executeCommand(command, timeout: timeout) { result in
                continuation.resume(with: result)
            }
        }
    }

    /// Example: Multiple commands with async/await
    @available(iOS 15.0, *)
    static func exampleAsyncExecution() async {
        do {
            print("🚀 Starting async command execution..."."🚀 Starting async command execution...")

            let hostname = try await executeCommandAsync("hostname"e"hostname")
            print("🖥️  Hostname: \(hostname)")"🖥️  Hostname: \(hostname)")

            let uptime = try await executeCommandAsync("uptime"e"uptime")
            print("⏰ Uptime: \(uptime)")"⏰ Uptime: \(uptime)")

            let diskUsage = try await executeCommandAsync("df -h /"/"df -h /")
            print("💾 Disk usage: \(diskUsage)")"💾 Disk usage: \(diskUsage)")

            print("✅ All commands completed successfully!"!"✅ All commands completed successfully!")

        } catch {
            print("❌ Error: \(error.localizedDescription)")"❌ Error: \(error.localizedDescription)")
        }
    }
}

// MARK: - Usage Examples

/*

 // Example 1: Simple command execution
 ISHCommandExecutor.executeCommand("ls -la"a"ls -la") { result in
     switch result {
     case .success(let output):
         print(output)
     case .failure(let error):
         print("Error: \(error)")"Error: \(error)")
     }
 }

 // Example 2: Multiple commands
 ISHCommandExecutor.exampleSystemInfo()

 // Example 3: Package installation
 ISHCommandExecutor.exampleInstallPackage()

 // Example 4: Async/await (iOS 15+)
 Task {
     await ISHCommandExecutor.exampleAsyncExecution()
 }

 // Example 5: Direct API usage
 ISHKernel.shared.executeCommandAndWait("echo 'Hello World'"'"echo 'Hello World'", timeout: 10.0) { output, error in
     if let output = output {
         print("Output: \(output)")"Output: \(output)")
     } else if let error = error {
         print("Error: \(error)")"Error: \(error)")
     }
 }

 */

#!/usr/bin/env ruby
# frozen_string_literal: true

# Add LaapCognitiveDebugPanel.swift to the Minis Xcode project.

require "xcodeproj"

project_path = File.expand_path("../src/ios/Minis.xcodeproj", __dir__)
file_path = File.expand_path("../src/ios/Views/Chat/LaapCognitiveDebugPanel.swift", __dir__)

project = Xcodeproj::Project.open(project_path)

# Find the "Chat" group nested under "Views".
views_group = project.main_group.recursive_children.find { |g| g.is_a?(Xcodeproj::Project::PBXGroup) && g.display_name == "Views" }
raise "Views group not found" unless views_group

chat_group = views_group.children.find { |g| g.is_a?(Xcodeproj::Project::PBXGroup) && g.display_name == "Chat" }
raise "Chat group not found" unless chat_group

# Find the main Minis application target.
target = project.targets.find { |t| t.name == "Minis" }
raise "Minis target not found" unless target

# Avoid duplicates.
existing = chat_group.files.find { |f| File.basename(f.path || "") == File.basename(file_path) }
if existing
  puts "[OK] #{File.basename(file_path)} already exists in Chat group; skipping."
  exit 0
end

file_ref = chat_group.new_file(File.basename(file_path))
target.source_build_phase.add_file_reference(file_ref)

project.save
puts "[OK] Added #{File.basename(file_path)} to Minis target Chat group."

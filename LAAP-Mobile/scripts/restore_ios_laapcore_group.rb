#!/usr/bin/env ruby
# frozen_string_literal: true

# Restore LAAPCore file references into the LAAPCore group after deduplication.

require "xcodeproj"

project_path = File.expand_path("../src/ios/Minis.xcodeproj", __dir__)
project = Xcodeproj::Project.open(project_path)

laapcore_group = project.main_group.recursive_children.find do |g|
  g.is_a?(Xcodeproj::Project::PBXGroup) && g.display_name == "LAAPCore"
end
raise "LAAPCore group not found" unless laapcore_group

basenames = %w[ArisEngineClient.swift CognitiveBus.swift CognitiveSpeciesLibrary.swift MobilePerceptionService.swift]

basenames.each do |basename|
  # Find existing file reference anywhere in the project.
  ref = project.files.find { |f| File.basename(f.path || "") == basename }
  unless ref
    puts "[WARN] File reference not found for #{basename}; skipping."
    next
  end

  if laapcore_group.children.include?(ref)
    puts "[INFO] #{basename} already in LAAPCore group; skipping."
    next
  end

  laapcore_group.children << ref
  puts "[INFO] Restored #{basename} to LAAPCore group."
end

project.save
puts "[OK] Restored LAAPCore group contents."

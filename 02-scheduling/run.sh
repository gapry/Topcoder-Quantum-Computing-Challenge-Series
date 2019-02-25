#!/usr/bin/env bash

declare -r py=/usr/bin/python3.7

function fmt() {
  yapf -i --style='{
    based_on_style: pep8, 
    indent_width: 2, 
    blank_lines_around_top_level_definition: 1
  }' main.py
}

function init() {
  clear
  fmt
}

function execute() {
  $py main.py
}

function main() {
  init
  execute
}

main

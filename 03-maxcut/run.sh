#!/usr/bin/env bash

declare -r py=/usr/bin/python3.7
declare -r src=main.py
declare -r submit=maxcut.zip

function fmt() {
  yapf -i --style='{
    based_on_style: pep8, 
    indent_width: 2, 
    blank_lines_around_top_level_definition: 1
  }' $src
}

function init() {
  clear
  fmt
}

function execute() {
  $py $src
}

function pre_submit() {
  rm -f *.zip
  zip -r $submit $src
}

function main() {
  init
  execute
  pre_submit
}

main

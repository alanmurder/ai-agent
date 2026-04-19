---
name: file_manager
version: 1.0.0
category: system
description: 文件管理和操作技能，支持文件读写、搜索、整理等功能
author: builtin
dependencies: []
permissions:
  - read_file
  - write_file
  - list_directory
tags:
  - file
  - system
  - personal
enabled: true
priority: 100
---

## 功能描述

文件管理技能提供文件系统的基本操作能力。

## 使用场景

- 用户需要读取或编辑文件
- 搜索特定文件
- 整理目录结构
- 创建或删除文件

## 工具列表

- `read_file`: 读取文件内容
- `write_file`: 写入文件内容
- `list_directory`: 列出目录内容
- `search_files`: 搜索文件
- `create_directory`: 创建目录
- `delete_file`: 删除文件
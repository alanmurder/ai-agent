---
name: product_manager
version: 1.0.0
category: ecommerce
description: 商品管理技能，提供商品信息管理、库存同步、价格策略等功能
author: builtin
dependencies: []
permissions:
  - read_product
  - write_product
  - manage_inventory
  - update_price
tags:
  - product
  - inventory
  - ecommerce
  - enterprise
enabled: true
priority: 85
---

## 功能描述

商品管理技能帮助电商直播公司管理商品信息和库存。

## 使用场景

- 商品信息查询和更新
- 库存实时同步
- 价格策略调整
- 商品上架管理
- SKU管理

## 工具列表

- `get_product_info`: 查询商品信息
- `update_product`: 更新商品信息
- `sync_inventory`: 同步库存
- `adjust_price`: 调整价格
- `list_products`: 商品列表查询
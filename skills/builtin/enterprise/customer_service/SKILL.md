---
name: customer_service
version: 1.0.0
category: ecommerce
description: 客服售后支持技能，提供自动回复、售后处理、订单查询、投诉处理等功能
author: builtin
dependencies: []
permissions:
  - read_order
  - handle_refund
  - respond_customer
  - process_complaint
tags:
  - customer
  - service
  - ecommerce
  - enterprise
enabled: true
priority: 80
---

## 功能描述

客服售后技能帮助电商直播公司处理客户服务。

## 使用场景

- 客户咨询自动回复
- 售后问题处理
- 订单状态查询
- 退款退货处理
- 投诉跟进

## 工具列表

- `query_order`: 查询订单信息
- `handle_refund`: 处理退款
- `auto_reply`: 自动回复客户
- `process_complaint`: 处理投诉
- `get_service_stats`: 客服统计
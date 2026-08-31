# 模板：MySQL 表结构 → MyBatis 映射生成（mysql-mapper）

> 适用：MySQL（非 HANA）场景下，从零建表 + 依据表结构元数据生成 Entity / Mapper 接口 / Mapper XML。
> 触发词：MySQL 建表、MyBatis 映射生成、表结构落地、数据访问层搭建。
> ⚠️ 本模板与 `data-mapper.md`（HANA + gen-mapper 工具）互斥：**MySQL 无 gen-mapper 可用**，必须由数据库工程师读 MySQL 元数据手工生成映射。

## 与 data-mapper 的关键差异

| 维度 | data-mapper（HANA） | mysql-mapper（MySQL） |
|------|---------------------|------------------------|
| 建表脚本 | HANA 语法（注意注释/类型差异） | MySQL 8 DDL，可 DROP+CREATE 重跑 |
| 映射来源 | gen-mapper 工具生成 | **读元数据**：`SHOW CREATE TABLE` / `DESCRIBE` / `INFORMATION_SCHEMA.COLUMNS` / `INFORMATION_SCHEMA.STATISTICS` |
| 校验手段 | 工具输出 | 自动化核对：COLUMNS ↔ resultMap ↔ 实体字段（javap 验证类型） |
| 金额字段 | DECIMAL 通用 | `DECIMAL(18,2)` + CHECK 约束（MySQL 8.0.16+ 生效）；实体用 BigDecimal |
| 索引验证 | EXPLAIN（HANA） | `EXPLAIN SELECT ...`（MySQL），确认 type/key 走索引 |

## 阶段序列

1. **数据库工程师**：设计 DDL（主键/唯一约束/索引/金额字段/CHECK）→ 执行建表 → 回读 `SHOW CREATE TABLE` 核对
2. **数据库工程师**：按元数据生成 Entity / Mapper 接口 / XML（包结构与项目约定一致；禁 Lombok 时手写 getter/setter；金额 BigDecimal、时间 LocalDateTime、状态 String）
3. **数据库工程师**：映射一致性三方核对（INFORMATION_SCHEMA ↔ resultMap ↔ 实体）+ EXPLAIN 关键查询走索引
4. **架构师/主 agent**：确认 Mapper 契约（方法签名清单）→ 供下游 Service 开发契约驱动接入
5. **质量工程师**：验收（映射一致、`#{}` 无 `${}`、只读 LIMIT、防 N+1）

## 数据库工程师关键约定（写进 prompt）

- **只读元数据生成，不依赖任何生成器工具**；DDL 执行需调度明确授权（限定库/表清单）
- SQL 全部 `#{}` 参数化，零 `${}`；单行查询带 `LIMIT 1`；列表查询（批量语义）显式注释豁免理由并约定调用方控制规模
- 乐观锁：`UPDATE ... SET status=#{...}, version=version+1 WHERE id=? AND version=?`（返回影响行数）
- 报表聚合：单条 SQL + `LIMIT #{offset},#{size}`；GROUP BY 用临时表/filesort 属预期，驱动条件必须走索引
- 防 N+1 接口：`selectByXxxIds(List<Long>)` IN 查询（调用方判空，防 `IN ()` 语法错误）
- 周期提醒：并发写文件场景（多子代理并行）遵守"只动自己包"边界，标注「预留」而非删除未用 API

## 沉淀案例

「订单中心」项目（T1 数据层）即按本模板执行：t_order/t_order_item/t_payment 三表 + 13 文件交付，EXPLAIN 全部走索引，映射一致性 ALL_MAPPING_CONSISTENT。

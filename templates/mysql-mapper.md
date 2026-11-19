# 模板：MySQL 建表 + MyBatis 映射（mysql-mapper）

> MySQL 场景：从零建表，再按元数据生成 Entity / Mapper 接口 / Mapper XML。
> 触发：MySQL 建表、MyBatis 映射生成、表结构落地、数据访问层搭建。

## 适用 / 不适用

- ✅ MySQL 8：从零建表 → 按元数据手写 Entity / Mapper 接口 / XML
- ✅ 没有 `gen-mapper`、需要落数据访问层的场景
- ❌ HANA 或环境里有 `gen-mapper` → `data-mapper`
- ❌ 只做查询分析、不动结构 → `research-query`

## 与 data-mapper 的互斥

| 维度 | data-mapper（HANA） | mysql-mapper（本模板） |
|------|---------------------|------------------------|
| 前提 | 有 `gen-mapper` | **没有** gen-mapper，全部手写 |
| 建表 | HANA DDL，谨慎 | MySQL 8 DDL，可 DROP+CREATE 重跑（需授权） |
| 映射来源 | 工具生成 | `SHOW CREATE TABLE` / `DESCRIBE` / `INFORMATION_SCHEMA` |
| 校验 | 工具输出 | COLUMNS ↔ resultMap ↔ 实体三方核对 |
| 金额 | DECIMAL | `DECIMAL(18,2)` + CHECK（8.0.16+ 生效）；实体 `BigDecimal` |
| 索引 | HANA EXPLAIN | `EXPLAIN SELECT`，确认 type/key |

**二选一，不要混着跑。**

## 规模

1 数据库 + 1 架构（可兼主 agent）+ 1 质量；开发仅在需要接 Service 时加入。

## 步骤序列

| 步骤 | 角色 | 要点 | 写域 |
|------|------|------|------|
| 1 | 架构师/主 agent | 确认库、表清单、包结构、是否允许 DDL | 无 |
| 2 | 数据库工程师 | 设计 DDL（主键/唯一/索引/金额/CHECK）→ **获授权后**执行 → 回读 `SHOW CREATE TABLE` 核对 | 迁移脚本目录 |
| 3 | 数据库工程师 | 按元数据生成 Entity / Mapper 接口 / XML（禁 Lombok 时手写 getter/setter） | 实体与 Mapper 包 |
| 4 | 数据库工程师 | 三方核对 + `EXPLAIN` 关键查询 | 同上 |
| 5 | 质量工程师 | 验收（映射一致、`#{}` 无 `${}`、LIMIT、防 N+1） | 无 |
| 6 | 主 agent | 报告 + 契约清单（方法签名 → 供 Service 接入） | `.team-mode/` |

## 数据库工程师的关键约定（写进 prompt）

- 只读元数据生成，**不依赖生成器工具**；DDL 执行须调度明确授权（限库限表）
- SQL 全部 `#{}`；单行查询带 `LIMIT 1`；列表查询显式注释豁免理由
- 乐观锁：`UPDATE ... SET status=#{s}, version=version+1 WHERE id=#{id} AND version=#{v}`，返回影响行数
- 报表聚合：单条 SQL + `LIMIT #{offset},#{size}`；驱动条件必须走索引
- 防 N+1：`selectByXxxIds(List<Long>)` + 调用方判空（防 `IN ()` 语法错误）
- 并行写文件时只动自己包，未用 API 标「预留」而非删除

## DoD

- DDL 可重复执行；回读结果与设计一致
- 三方一致（附核对结果）
- EXPLAIN 显示关键查询走索引
- Mapper 方法签名清单已交给下游

## 输出

表结构、生成文件清单、映射一致性结论、索引验证结果、Service 接入契约。

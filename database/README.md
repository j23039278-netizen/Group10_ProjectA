# SEAGAS — Database Schema Reference
**Author:** Soh Way Miin (Carl) · Backend Developer  
**Group 10 · COS40005 · Swinburne University**

---

## 📋 Tables Overview

| # | Table | 用途 | FR |
|---|-------|------|----|
| 1 | `users` | 所有用户账号（student/advisor/admin）+ 认证 | NFR-04 |
| 2 | `student_profiles` | 学生基本信息、GPA、目标职位 | FR-01 |
| 3 | `skills_library` | 166 个技能（138 个 IT + 28 个 Business，下拉菜单来源），含 `subcategory` 和 `source`（v1/v2/v3） | FR-02 |
| 4 | `student_skills` | 学生拥有的技能（profile × skill） | FR-01, FR-02 |
| 5 | `job_roles` | 6 个 IT 职位模板 | FR-03 |
| 5b | `job_role_skills` | 每个职位需要的技能 | FR-03 |
| 6 | `job_descriptions` | 学生上传/粘贴的 JD 原文 | FR-03, FR-04 |
| 6b | `jd_extracted_skills` | NLP 从 JD 提取的技能 | FR-04 |
| 7 | `assessments` | 每次评估的总分 + 7个维度分数 | FR-07, FR-08 |
| 7b | `skill_match_results` | 每个技能的匹配结果（strong/developing/gap） | FR-09 |
| 8 | `recommendations_library` | 推荐资源库（课程、认证、项目） | FR-10 |
| 9 | `student_recommendations` | 每次评估推荐给学生的资源（目前后端还没有写入） | FR-10 |
| 10 | `student_projects` | 学生的项目记录 | FR-01 |
| 11 | `student_certifications` | 学生的认证记录 | FR-01 |
| 12 | `student_resource_progress` | 学生对推荐资源的 Start / Complete 进度（`progress.py` 写入，`v_student_progress` 读取） | FR-11 |

---

## 🔗 Table Relationships

```
users (1) ──────────── (1) student_profiles
                                │
                    ┌───────────┼───────────────┐
                    │           │               │
             student_skills  job_descriptions  assessments
                    │           │               │
             skills_library  jd_extracted_skills  skill_match_results
                    │                            │
             recommendations_library         student_recommendations
                    │
             job_role_skills ──── job_roles
```

---

## 🗝️ Key Design Decisions

### 1. UUID as Primary Keys
所有 PK 用 UUID，不用 auto-increment integer  
原因：分布式友好，不暴露数据量，安全性更高

### 2. Skill Status: strong / developing / gap
存在 `skill_match_results.match_status`  
由 NLP 匹配引擎写入，不是学生手动填的

### 3. 7-Dimension Score
在 `assessments` 表里有 7 个独立分数列：  
`score_technical`, `score_ai_digital`, `score_analytical`,  
`score_communication`, `score_industry_exp`, `score_project_exp`, `score_certification`

### 4. Level 1 vs Level 2 都记录
`matching_method` 字段在 `assessments` 和 `skill_match_results` 都有  
值：`'keyword'` | `'semantic'` | `'hybrid'`  
用于 FR-14 的 AI evaluation report 对比

---

## ⚙️ Setup Instructions

### 1. 安装依赖
```bash
pip install sqlalchemy psycopg2-binary alembic
```

### 2. 创建数据库
```bash
psql -U postgres
CREATE DATABASE seagas_db;
\q
```

### 3. 运行 Schema
```bash
psql -U postgres -d seagas_db -f schema.sql
```

### 4. 验证表是否创建成功
```bash
psql -U postgres -d seagas_db -c "\dt"
```
你应该看到 15 张表 + 3 个 view

### 5. 已有旧数据库？
`schema.sql` 只在新数据库上运行。旧数据库请运行（`start_backend.bat` 每次启动会自动运行）：
```bash
psql -U postgres -d seagas_db -f migrate_existing_db.sql
```

---

## 📌 谁需要用这个

| 成员 | 用途 |
|------|------|
| Carl (你) | FastAPI endpoints 对接这些 models |
| Yong Hin | `jd_extracted_skills`, `skill_match_results` 写入 |
| Aaron | `recommendations_library`, `student_recommendations` 查询 |
| Ren Hang | 通过 API 读取 `v_cohort_skill_gaps` view |
| Shanice | 通过 API 读取 `assessments` + `skill_match_results` |

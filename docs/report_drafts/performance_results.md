# Performance test results (S3-06)

Measured 2026-11-16T12:37:59 with `tests/performance/perf_run.py` on a copy of the local database.
Target: an assessment returns within **5 s** (the S3-06 response-time target).

**Data:** 5,012 students, 5,043 assessments, 154,628 skill results, 172 skills, 388 job descriptions.  
**Machine:** Windows 11, 12 logical CPUs (AMD64 Family 25 Model 68 Stepping 1, AuthenticAMD), Python 3.12.5; backend (uvicorn, 1 worker) and PostgreSQL 17 on the same laptop; requests over HTTP on localhost.  
**Backend start-up:** the API answers 1.6 s after it is started. The NLP model then loads in a background thread; a hybrid request sent at once waited **14.27 s** for it, and the model was ready 16.0 s after start. This happens once per start (e.g. after a deployment); every request below was timed after that.

| Request | Group | n | Mean (s) | Median (s) | P95 (s) | Max (s) | Within 5 s | Note |
|---|---|---:|---:|---:|---:|---:|---|---|
| Sign in (student) | Student | 20 | 0.073 | 0.077 | 0.083 | 0.083 | Yes |  |
| Run assessment, role template (keyword) | Assessment | 20 | 0.024 | 0.020 | 0.039 | 0.048 | Yes | method used: keyword |
| Run assessment, role template (hybrid) | Assessment | 20 | 0.021 | 0.015 | 0.034 | 0.034 | Yes | method used: hybrid |
| Recommendations for an assessment | Assessment | 20 | 0.030 | 0.033 | 0.041 | 0.042 | Yes |  |
| Paste a job description and extract its skills (hybrid) | Job description | 10 | 0.075 | 0.074 | 0.102 | 0.102 | Yes |  |
| Run assessment against the pasted job description (hybrid) | Job description | 10 | 0.021 | 0.014 | 0.039 | 0.039 | Yes |  |
| Upload a CV and extract its skills (hybrid) | CV | 10 | 0.085 | 0.085 | 0.101 | 0.101 | Yes |  |
| Student profile | Student pages | 20 | 0.012 | 0.011 | 0.024 | 0.027 | Yes |  |
| Assessment history | Student pages | 20 | 0.014 | 0.008 | 0.031 | 0.031 | Yes |  |
| Learning progress | Student pages | 20 | 0.014 | 0.015 | 0.026 | 0.029 | Yes |  |
| Career paths (all roles of the course) | Student pages | 20 | 0.025 | 0.029 | 0.033 | 0.036 | Yes |  |
| Cohort overview (status of every student) | Advisor pages | 10 | 0.200 | 0.195 | 0.247 | 0.247 | Yes |  |
| Student list (all students of the courses) | Advisor pages | 10 | 0.289 | 0.263 | 0.518 | 0.518 | Yes |  |
| Skill gaps (latest assessment of every student) | Advisor pages | 10 | 0.139 | 0.134 | 0.204 | 0.204 | Yes |  |
| MQF clusters (every skill result) | Advisor pages | 10 | 0.120 | 0.113 | 0.175 | 0.175 | Yes |  |
| Learning progress (cohort) | Advisor pages | 10 | 0.022 | 0.028 | 0.037 | 0.037 | Yes |  |
| 10 hybrid assessments at the same time | Concurrency | 10 | 0.195 | 0.191 | 0.278 | 0.278 | Yes | all 10 done in 0.29 s |

All 17 measured requests meet the 5 s target at P95: yes.
The slowest is "Student list (all students of the courses)" (P95 0.52 s).

Notes: times are measured by the client over HTTP on the same machine, so network delay to a real
server is not included. Each request is timed separately after one warm-up assessment; the start-up
time is reported on its own because the model is loaded only once when the backend starts.

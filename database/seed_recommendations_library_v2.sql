-- ============================================================
-- SEAGAS — Recommendations Library v2 (Web Developer Skills)
-- Adds resources for skills missing from v1
-- Author: Tan Jun Xiong (Aaron) — Recommendation Engine
-- Run: psql -U postgres -d seagas_db -f database/seed_recommendations_library_v2.sql
-- ============================================================

INSERT INTO recommendations_library
    (skill_id, resource_title, resource_type, provider, url, duration_hours, cost, difficulty, description)

SELECT sl.skill_id, r.resource_title, r.resource_type, r.provider, r.url, r.duration_hours, r.cost, r.difficulty, r.description
FROM skills_library sl
JOIN (VALUES

-- ── HTML / CSS ────────────────────────────────────────────────
('HTML',         'Responsive Web Design Certification',           'certification', 'freeCodeCamp',              'https://www.freecodecamp.org/learn/2022/responsive-web-design/',       300, 'Free',          'beginner',      'Full HTML and CSS certification including flexbox, grid and responsive design.'),
('HTML',         'HTML and CSS for Beginners',                    'course',        'Udemy',                     'https://www.udemy.com/course/html-and-css-for-beginners-crash-course-learn-fast-easy/', 5, 'Free', 'beginner', 'Quick and practical HTML and CSS crash course for beginners.'),
('HTML',         'Build a Personal Portfolio Website',            'project',       'Self-directed',             'https://www.freecodecamp.org/learn',                                   10,  'Free',          'beginner',      'Build a personal portfolio website using HTML and CSS to showcase your projects.'),

('CSS',          'CSS Grid and Flexbox for Responsive Layouts',   'course',        'Udemy',                     'https://www.udemy.com/course/css-flexbox-and-grid/',                   6,   'Paid ~$15',     'intermediate',  'Master modern CSS layout techniques including flexbox and grid.'),
('CSS',          'CSS — The Complete Guide',                      'course',        'Udemy / Maximilian',        'https://www.udemy.com/course/css-the-complete-guide-incl-flexbox-grid-sass/', 22, 'Paid ~$15', 'beginner',  'Comprehensive CSS course from basics to animations and SASS.'),
('CSS',          'Style a React Dashboard Project',               'project',       'Self-directed',             'https://tailwindcss.com/docs/installation',                            8,   'Free',          'intermediate',  'Apply a consistent CSS framework (Tailwind or Bootstrap) to a React project.'),

-- ── TYPESCRIPT ───────────────────────────────────────────────
('TypeScript',   'Understanding TypeScript',                      'course',        'Udemy / Maximilian',        'https://www.udemy.com/course/understanding-typescript/',               22,  'Paid ~$15',     'intermediate',  'Complete TypeScript course covering types, generics, decorators and React integration.'),
('TypeScript',   'TypeScript Official Handbook',                  'course',        'Microsoft',                 'https://www.typescriptlang.org/docs/handbook/intro.html',             10,  'Free',          'beginner',      'Official TypeScript documentation and learning guide.'),
('TypeScript',   'Convert a JavaScript Project to TypeScript',    'project',       'Self-directed',             'https://www.typescriptlang.org/docs/handbook/migrating-from-javascript.html', 8, 'Free', 'intermediate', 'Migrate an existing JavaScript project to TypeScript as a portfolio exercise.'),

-- ── MONGODB ──────────────────────────────────────────────────
('MongoDB',      'MongoDB Atlas Developer Certification',         'certification', 'MongoDB',                   'https://learn.mongodb.com/pages/mongodb-associate-developer-exam', 20,   '$150 USD',      'intermediate',  'Official MongoDB developer certification for CRUD operations and schema design.'),
('MongoDB',      'MongoDB University Free Courses',               'course',        'MongoDB',                   'https://learn.mongodb.com/',                                          10,  'Free',          'beginner',      'Free official MongoDB courses covering basics, aggregation and indexing.'),
('MongoDB',      'Build a REST API with Node.js and MongoDB',     'project',       'Self-directed',             'https://www.mongodb.com/developer/languages/javascript/',             15,  'Free',          'intermediate',  'Build a full CRUD REST API using Node.js, Express and MongoDB Atlas.'),

-- ── VUE.JS ───────────────────────────────────────────────────
('Vue.js',       'Vue — The Complete Guide',                      'course',        'Udemy / Maximilian',        'https://www.udemy.com/course/vuejs-2-the-complete-guide/',            32,  'Paid ~$15',     'intermediate',  'Complete Vue.js course covering Vue 3, Vuex, Vue Router and Composition API.'),
('Vue.js',       'Vue.js Official Documentation',                 'course',        'Vue.js',                    'https://vuejs.org/guide/introduction.html',                           10,  'Free',          'beginner',      'Official Vue.js guide and documentation for building reactive web applications.'),
('Vue.js',       'Build a Task Management App with Vue',          'project',       'Self-directed',             'https://vuejs.org/tutorial/',                                         12,  'Free',          'intermediate',  'Build a task management or to-do application using Vue 3 and Pinia.'),

-- ── NODE.JS ──────────────────────────────────────────────────
('Node.js',      'The Complete Node.js Developer Course',         'course',        'Udemy / Andrew Mead',       'https://www.udemy.com/course/the-complete-nodejs-developer-course-2/', 35, 'Paid ~$15',    'intermediate',  'Complete Node.js course covering Express, MongoDB, REST APIs and authentication.'),
('Node.js',      'Node.js Official Documentation',                'course',        'Node.js',                   'https://nodejs.org/en/learn/getting-started/introduction-to-nodejs', 8,   'Free',         'beginner',      'Official Node.js documentation and getting started guide.'),
('Node.js',      'Build a REST API with Node.js and Express',     'project',       'Self-directed',             'https://expressjs.com/en/starter/hello-world.html',                   12,  'Free',          'intermediate',  'Build and document a RESTful API using Node.js, Express and a database.'),

-- ── EXPRESS.JS ───────────────────────────────────────────────
('Express.js',   'Node.js and Express.js — Full Course',          'course',        'freeCodeCamp / YouTube',    'https://www.youtube.com/watch?v=Oe421EPjeBE',                         8,   'Free',          'beginner',      'Free 8-hour Node.js and Express.js full course on YouTube by freeCodeCamp.'),
('Express.js',   'Build a JWT Authentication API',                'project',       'Self-directed',             'https://expressjs.com/en/guide/routing.html',                         10,  'Free',          'intermediate',  'Build a complete authentication system using Express.js and JWT tokens.'),

-- ── PHP ──────────────────────────────────────────────────────
('PHP',          'PHP for Beginners',                             'course',        'Laracasts',                 'https://laracasts.com/series/php-for-beginners-2023-edition',         10,  'Free',          'beginner',      'Free beginner PHP series on Laracasts covering modern PHP development.'),
('PHP',          'Build a PHP CRUD Application',                  'project',       'Self-directed',             'https://www.php.net/manual/en/tutorial.php',                          10,  'Free',          'beginner',      'Build a simple CRUD web application using PHP and MySQL.'),

-- ── GRAPHQL ──────────────────────────────────────────────────
('GraphQL',      'GraphQL with React: The Complete Developers Guide', 'course',    'Udemy / Stephen Grider',    'https://www.udemy.com/course/graphql-with-react-course/',             13,  'Paid ~$15',     'intermediate',  'Learn GraphQL by building real-world React applications.'),
('GraphQL',      'GraphQL Official Documentation',                'course',        'GraphQL',                   'https://graphql.org/learn/',                                           6,   'Free',          'beginner',      'Official GraphQL learning guide and documentation.'),

-- ── REST API ─────────────────────────────────────────────────
('REST API',     'REST API Design Best Practices',                'course',        'Udemy',                     'https://www.udemy.com/course/rest-api/',                              4,   'Paid ~$15',     'intermediate',  'Learn REST API design principles and best practices.'),
('REST API',     'Build and Document a REST API',                 'project',       'Self-directed',             'https://swagger.io/docs/specification/basic-structure/',              10,  'Free',          'intermediate',  'Build a REST API and document it with Swagger/OpenAPI specification.'),

-- ── UI/UX DESIGN ─────────────────────────────────────────────
('UI/UX Design', 'Google UX Design Certificate',                  'certification', 'Coursera / Google',         'https://www.coursera.org/professional-certificates/google-ux-design', 240, 'Free to audit', 'beginner',    'Six-month Google UX design professional certificate covering the full design process.'),
('UI/UX Design', 'UI / UX Design Bootcamp',                       'course',        'Udemy',                     'https://www.udemy.com/course/ui-ux-design-bootcamp/',                20,  'Paid ~$15',     'beginner',      'Complete UI/UX design bootcamp covering Figma, wireframing and prototyping.'),
('UI/UX Design', 'Design a Mobile App in Figma',                  'project',       'Self-directed',             'https://www.figma.com/resources/learn-design/',                       12,  'Free',          'beginner',      'Design a complete mobile app UI in Figma including wireframes and prototype.'),

-- ── UNIT TESTING ─────────────────────────────────────────────
('Unit Testing',  'JavaScript Unit Testing — The Practical Guide', 'course',       'Udemy / Maximilian',        'https://www.udemy.com/course/javascript-unit-testing-the-practical-guide/', 8, 'Paid ~$15', 'intermediate', 'Learn unit and integration testing with Jest and Vitest.'),
('Unit Testing',  'Write Unit Tests for a React App',              'project',       'Self-directed',             'https://jestjs.io/docs/getting-started',                              8,   'Free',          'intermediate',  'Write unit and integration tests for an existing React application using Jest.'),

-- ── AGILE / SCRUM ────────────────────────────────────────────
('Agile / Scrum', 'Professional Scrum Master I (PSM I)',           'certification', 'Scrum.org',                 'https://www.scrum.org/assessments/professional-scrum-master-i-certification', 10, '$150 USD', 'intermediate', 'Entry-level Scrum Master certification from Scrum.org.'),
('Agile / Scrum', 'Agile Crash Course: Agile Project Management',  'course',        'Udemy',                     'https://www.udemy.com/course/agile-crash-course/',                    3,   'Free',          'beginner',      'Quick introduction to agile and Scrum methodology.'),

-- ── PROBLEM SOLVING ──────────────────────────────────────────
('Problem Solving', 'LeetCode Problem Solving Practice',           'course',        'LeetCode',                  'https://leetcode.com/study-plan/leetcode-75/',                        30,  'Free / Paid',   'intermediate',  'Structured LeetCode 75 study plan covering essential data structures and algorithms.'),
('Problem Solving', 'Solve 30 LeetCode Easy Problems',             'project',       'Self-directed',             'https://leetcode.com/problemset/?difficulty=EASY',                    20,  'Free',          'beginner',      'Complete 30 easy LeetCode problems to build problem solving confidence and skills.'),

-- ── FIGMA ────────────────────────────────────────────────────
('Figma',        'Figma UI UX Design Essentials',                  'course',        'Udemy',                     'https://www.udemy.com/course/figma-ux-ui-design-user-experience-tutorial-course/', 12, 'Paid ~$15', 'beginner', 'Learn Figma from scratch for UI/UX design and prototyping.'),
('Figma',        'Figma for Beginners Tutorial',                   'course',        'Figma',                     'https://www.youtube.com/playlist?list=PLXDU_eVOJTx7QHLShNqIXL1Cgbxj7HlN4', 5, 'Free', 'beginner', 'Official Figma beginner tutorial series on YouTube.'),
('Figma',        'Design a Website Prototype in Figma',            'project',       'Self-directed',             'https://www.figma.com/templates/',                                    10,  'Free',          'beginner',      'Design a complete website prototype with responsive layouts in Figma.')

) AS r(skill_name, resource_title, resource_type, provider, url, duration_hours, cost, difficulty, description)
ON sl.skill_name = r.skill_name
WHERE sl.is_active = TRUE

ON CONFLICT DO NOTHING;

-- ── VERIFY ───────────────────────────────────────────────────
SELECT COUNT(*) AS total_resources FROM recommendations_library;

SELECT sl.skill_name, COUNT(rl.resource_id) AS resources
FROM skills_library sl
LEFT JOIN recommendations_library rl ON rl.skill_id = sl.skill_id
GROUP BY sl.skill_name
HAVING COUNT(rl.resource_id) = 0
ORDER BY sl.skill_name
LIMIT 20;

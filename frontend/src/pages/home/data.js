// SEAGAS Home — demo / sample data for the landing page.
// None of this is real student data; every card that uses it is labelled "Sample" or "Demo".

export const STATUS_LABEL = { strong: 'Strong', developing: 'Developing', gap: 'Gap' }

// Hero role switcher
export const HERO_ROLES = [
  {
    id: 'cloud', role: 'Cloud Engineer', score: 78, strong: 9, developing: 3, gap: 2,
    skills: [['AWS', 'strong'], ['Python', 'strong'], ['Linux', 'strong'], ['Docker', 'developing'], ['Kubernetes', 'gap']],
  },
  {
    id: 'data', role: 'Data Analyst', score: 64, strong: 7, developing: 4, gap: 3,
    skills: [['Python', 'strong'], ['SQL', 'strong'], ['Excel', 'strong'], ['Power BI', 'developing'], ['Statistics', 'developing'], ['Tableau', 'gap']],
  },
  {
    id: 'software', role: 'Software Developer', score: 71, strong: 8, developing: 4, gap: 2,
    skills: [['Java', 'strong'], ['Git', 'strong'], ['OOP', 'strong'], ['React', 'developing'], ['Testing', 'developing'], ['Docker', 'gap']],
  },
]

// Floating, clickable skill tags around the hero.
// `pos` is the CSS position inside the hero; `dur` is the float duration.
export const FLOAT_SKILLS = [
  { name: 'Python',           tip: 'Programming skill',         category: 'Programming',        roles: ['Data Analyst', 'Software Developer'], pos: { top: '15%', left: '4%' },     dur: 5,   tier: 1 },
  { name: 'AWS',              tip: 'Cloud computing skill',     category: 'Cloud Computing',    roles: ['Cloud Engineer', 'DevOps Engineer'],  pos: { top: '12%', left: '46%' },    dur: 6,   tier: 1 },
  { name: 'SQL',              tip: 'Data querying skill',       category: 'Data & Databases',   roles: ['Data Analyst', 'Data Scientist'],     pos: { top: '47%', left: '3%' },   dur: 4.5, tier: 2 },
  { name: 'Power BI',         tip: 'Data visualisation skill',  category: 'Data Visualisation', roles: ['Data Analyst', 'Business Analyst'],   pos: { top: '14%', right: '5%' },    dur: 5.8, tier: 1 },
  { name: 'Machine Learning', tip: 'AI / data science skill',   category: 'AI & Digital',       roles: ['Data Scientist', 'AI / ML Engineer'], pos: { bottom: '5%', left: '3%' },  dur: 6.4, tier: 1 },
  { name: 'Communication',    tip: 'Soft skill',                category: 'Soft Skills',        roles: ['Every IT role'],                      pos: { bottom: '5%', left: '30%' },  dur: 5.2, tier: 2 },
  { name: 'Docker',           tip: 'Containerisation skill',    category: 'DevOps & Cloud',     roles: ['Cloud Engineer', 'Software Developer'], pos: { bottom: '13%', right: '9%' }, dur: 5.5, tier: 1 },
  { name: 'Linux',            tip: 'Operating systems skill',   category: 'Systems & Security', roles: ['Cybersecurity Analyst', 'Cloud Engineer'], pos: { top: '52%', right: '3%' }, dur: 4.8, tier: 2 },
]

// How it works
export const STEPS = [
  { id: 'profile', title: 'Build your profile',  text: 'Add your academic background, GPA, skills, projects and certifications. This is what SEAGAS compares against the job.' },
  { id: 'career',  title: 'Choose your career',  text: 'Pick one of the IT role templates or paste a real job description. SEAGAS extracts the skills the job asks for.' },
  { id: 'compare', title: 'Compare your skills', text: 'Your skills are matched against the job requirements, including related skills, not just exact keywords.' },
  { id: 'gaps',    title: 'Find your gaps',      text: 'Every required skill is sorted into Strong, Developing or Gap, so you know exactly what to work on next.' },
]

// Skill matching demo — two directions give two different analyses
export const DEMO_YOUR_SKILLS = ['Python', 'React', 'Git', 'SQL']
export const DEMO_JOB_SKILLS = ['Python', 'React', 'AWS', 'Docker', 'Linux']
export const DEMO_MODES = {
  // Your skills -> job requirements: are you ready for this job?
  readiness: {
    question: 'Are you ready for this job?',
    stages: ['Scanning skills...', 'Comparing job requirements...', 'Matching skills...', 'Calculating readiness...'],
    groups: [
      { key: 'strong',     label: 'Strong',     skills: ['Python', 'React'] },
      { key: 'developing', label: 'Developing', skills: ['SQL'] },
      { key: 'gap',        label: 'Gap',        skills: ['AWS', 'Docker', 'Linux'] },
    ],
    summary: '2 of 5 job requirements already met. Build AWS, Docker and Linux next.',
  },
  // Job requirements -> your skills: which of your skills does this job use?
  relevance: {
    question: 'Which of your skills does this job use?',
    stages: ['Reading job requirements...', 'Scanning your skills...', 'Checking relevance...', 'Ranking your skills...'],
    groups: [
      { key: 'strong',     label: 'Relevant',     skills: ['Python', 'React'] },
      { key: 'developing', label: 'Transferable', skills: ['Git'] },
      { key: 'neutral',    label: 'Not required', skills: ['SQL'] },
    ],
    summary: '2 of your 4 skills are used directly. Git supports the Docker and Linux workflow.',
  },
}

// Skill gap preview (alignment values are 0–100)
export const GAP_SKILLS = [
  { name: 'Python', current: 95, required: 80, action: 'Already job-ready. Keep it sharp with a portfolio project.' },
  { name: 'SQL',    current: 84, required: 75, action: 'Strong. Add an advanced query or data-modelling project.' },
  { name: 'AWS',    current: 60, required: 85, action: 'Start the AWS Cloud Practitioner certification.' },
  { name: 'Docker', current: 40, required: 75, action: 'Containerise one of your existing projects.' },
  { name: 'Linux',  current: 30, required: 70, action: 'Practise daily command-line tasks and shell scripting.' },
]

export function gapStatus(skill) {
  const gap = skill.required - skill.current
  if (gap <= 0) return 'strong'
  if (gap < 30) return 'developing'
  return 'gap'
}

// Career role cards (the role names match the SEAGAS job role templates)
export const CAREER_ROLES = [
  { id: 'cloud',  icon: 'cloud',  role: 'Cloud Engineer',        blurb: 'Design and run cloud infrastructure.',        core: ['AWS', 'Azure', 'Linux', 'Docker', 'Terraform'],        gaps: ['Kubernetes', 'Networking'],     score: 78 },
  { id: 'data',   icon: 'chart',  role: 'Data Analyst',          blurb: 'Turn data into business insights.',           core: ['Python', 'SQL', 'Excel', 'Power BI', 'Statistics'],    gaps: ['Tableau', 'Data Modelling'],    score: 64 },
  { id: 'soft',   icon: 'code',   role: 'Software Developer',    blurb: 'Design and build software applications.',     core: ['Java', 'Git', 'OOP', 'React', 'Testing'],              gaps: ['Docker', 'CI/CD'],              score: 71 },
  { id: 'cyber',  icon: 'shield', role: 'Cybersecurity Analyst', blurb: 'Protect systems from security threats.',      core: ['Linux', 'Networking', 'Wireshark', 'SIEM', 'Python'],  gaps: ['Nmap', 'Incident Response'],    score: 58 },
  { id: 'sci',    icon: 'brain',  role: 'Data Scientist',        blurb: 'Build machine learning models.',              core: ['Python', 'Machine Learning', 'Pandas', 'Statistics'],  gaps: ['TensorFlow', 'MLOps'],          score: 55 },
  { id: 'web',    icon: 'globe',  role: 'Web Developer',         blurb: 'Build modern websites and web apps.',         core: ['JavaScript', 'React', 'HTML/CSS', 'Git', 'REST APIs'], gaps: ['TypeScript', 'Testing'],        score: 69 },
]

// Recommendation preview
export const NEXT_STEPS = [
  { gap: 'AWS',      title: 'AWS Cloud Practitioner Certification', type: 'Certification', provider: 'AWS Skill Builder', difficulty: 'Beginner', hours: 40, cost: '$100 USD' },
  { gap: 'Power BI', title: 'Microsoft Power BI Fundamentals',      type: 'Course',        provider: 'Microsoft Learn',   difficulty: 'Beginner', hours: 8,  cost: 'Free' },
  { gap: 'Docker',   title: 'Containerise a portfolio project',     type: 'Project',       provider: 'Self-guided',       difficulty: 'Intermediate', hours: 12, cost: 'Free' },
]

// Progress preview (three example assessments)
export const PROGRESS_DATA = [
  { name: 'Assessment 1', readiness: 52, strong: 5, developing: 4, gap: 5, completed: 0 },
  { name: 'Assessment 2', readiness: 64, strong: 7, developing: 4, gap: 3, completed: 3 },
  { name: 'Assessment 3', readiness: 78, strong: 9, developing: 3, gap: 2, completed: 6 },
]

// Who it's for
export const AUDIENCES = [
  {
    id: 'students', icon: 'student', title: 'Students',
    text: 'Understand your career readiness and skill gaps.',
    points: ['Job Readiness Score across 7 dimensions', 'Strong / Developing / Gap breakdown', 'Courses, certifications and projects to close gaps'],
  },
  {
    id: 'advisors', icon: 'advisor', title: 'Advisors',
    text: 'Identify student and cohort skill gaps.',
    points: ['Cohort readiness overview', 'Most common skill gaps', 'Full student list and progress'],
  },
  {
    id: 'universities', icon: 'university', title: 'Universities',
    text: 'Understand employability trends.',
    points: ['Readiness trends across cohorts', 'Skills most demanded by industry roles', 'Evidence to guide curriculum decisions'],
  },
]

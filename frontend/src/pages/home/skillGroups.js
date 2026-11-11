// SEAGAS Home — skill groups used to colour skill tags (marquee, skill-analysis demo).
// Each group has its own colour in Home.css (.hp-sg-<group>), so a skill looks the same everywhere.
export const SKILL_GROUP = {
  code:  ['Python', 'JavaScript', 'React', 'Git', 'Java', 'OOP', 'Testing'],
  cloud: ['AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Terraform', 'Linux', 'CI/CD'],
  data:  ['SQL', 'Power BI', 'Tableau', 'Machine Learning', 'TensorFlow', 'PyTorch', 'Pandas', 'NumPy', 'Generative AI',
          'Excel', 'Statistics', 'Data Modelling', 'MLOps'],
  sec:   ['Wireshark', 'Nmap', 'SIEM', 'Networking', 'Incident Response'],
  soft:  ['Critical Thinking', 'Communication', 'Teamwork', 'Project Management'],
}

export const groupOf = (skill) =>
  Object.keys(SKILL_GROUP).find(g => SKILL_GROUP[g].includes(skill)) || 'code'

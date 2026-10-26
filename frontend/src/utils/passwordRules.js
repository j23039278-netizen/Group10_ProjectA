// SEAGAS — Password rules, the same ones the backend enforces (password_error in
// backend/routers/auth.py). The backend has the final say; this is for instant feedback.
export const PASSWORD_RULES = [
  { id: 'length', text: 'At least 8 characters',  test: pw => pw.length >= 8 },
  { id: 'upper',  text: 'An uppercase letter',    test: pw => /[A-Z]/.test(pw) },
  { id: 'lower',  text: 'A lowercase letter',     test: pw => /[a-z]/.test(pw) },
  { id: 'digit',  text: 'A number',               test: pw => /[0-9]/.test(pw) },
  { id: 'symbol', text: 'A symbol, e.g. ! @ # $', test: pw => /[^A-Za-z0-9\s]/.test(pw) },
]

export const PASSWORD_RULE_TEXT = 'at least 8 characters, with an uppercase letter, a lowercase letter, a number and a symbol'

// null when the password meets every rule, otherwise a message to show
export function passwordProblem(pw) {
  if (new TextEncoder().encode(pw).length > 72) return 'Password must be at most 72 bytes.'
  return PASSWORD_RULES.every(r => r.test(pw)) ? null : `Password must have ${PASSWORD_RULE_TEXT}.`
}

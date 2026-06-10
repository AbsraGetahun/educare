// Strong password rules for EDUCARE (real-time checklist + strength)
// Matches backend validate_strong_password

export const PASSWORD_RULES = {
  minLength: 8,
  maxLength: 20,
  requireUpper: true,
  requireLower: true,
  requireDigit: true,
  requireSpecial: true,
  specialChars: '!@#$%^&*',
};

export function getPasswordStrength(password) {
  if (!password) return { score: 0, label: 'Weak', color: 'red' };
  
  let score = 0;
  const len = password.length;
  
  if (len >= 8) score += 1;
  if (len >= 12) score += 1;
  if (/[A-Z]/.test(password)) score += 1;
  if (/[a-z]/.test(password)) score += 1;
  if (/[0-9]/.test(password)) score += 1;
  if (/[!@#$%^&*]/.test(password)) score += 1;
  if (len >= 16) score += 1;
  
  let label, color;
  if (score <= 2) { label = 'Weak'; color = '#ef4444'; }
  else if (score <= 4) { label = 'Medium'; color = '#f59e0b'; }
  else { label = 'Strong'; color = '#10b981'; }
  
  return { score: Math.min(score, 6), label, color, percent: Math.round((score / 6) * 100) };
}

export function checkPasswordRules(password) {
  const p = password || '';
  return {
    length: p.length >= PASSWORD_RULES.minLength && p.length <= PASSWORD_RULES.maxLength,
    upper: /[A-Z]/.test(p),
    lower: /[a-z]/.test(p),
    digit: /[0-9]/.test(p),
    special: /[!@#$%^&*]/.test(p),
  };
}

export function validatePassword(password) {
  const rules = checkPasswordRules(password);
  const allOk = Object.values(rules).every(Boolean);
  const strength = getPasswordStrength(password);
  const errors = [];
  if (!rules.length) errors.push(`8-20 characters`);
  if (!rules.upper) errors.push('1 uppercase letter');
  if (!rules.lower) errors.push('1 lowercase letter');
  if (!rules.digit) errors.push('1 number');
  if (!rules.special) errors.push('1 special (!@#$%^&*)');
  return { isValid: allOk, rules, strength, errors };
}

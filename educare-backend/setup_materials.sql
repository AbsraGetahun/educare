-- Sample pending materials for testing Teacher Content Approval Workflow
-- These materials will be inserted with status 'Pending' for teacher approval

-- First, ensure the material table exists
CREATE TABLE IF NOT EXISTS material (
    material_id INT AUTO_INCREMENT PRIMARY KEY,
    topic_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    source_citation VARCHAR(500),
    approval_status ENUM('Pending', 'Approved', 'Rejected') DEFAULT 'Pending',
    generated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (topic_id) REFERENCES topics(topic_id) ON DELETE CASCADE
);

-- Insert sample pending materials for Algebra (topic_id = 1)
INSERT INTO material (topic_id, title, content, source_citation, approval_status) VALUES
(1, 'Algebra Practice Exercises - Linear Equations', 
'Practice solving linear equations:

1. Solve for x: 3x + 7 = 22
2. Solve for y: 5y - 3 = 17
3. Solve for z: 2z + 8 = 3z - 4
4. Solve for a: 4(a - 2) = 3a + 5
5. Solve for b: 6b + 3 = 2b + 19

Tips:
- Isolate the variable on one side
- Perform the same operation on both sides
- Check your answer by substituting back',
'EDUCARE Mathematics Department', 'Pending'),

(1, 'Algebra Practice Exercises - Quadratic Equations',
'Practice solving quadratic equations:

1. Solve: x² - 5x + 6 = 0
2. Solve: x² + 3x - 10 = 0
3. Solve: 2x² - 7x + 3 = 0
4. Solve: x² - 9 = 0
5. Solve: x² + 6x + 9 = 0

Methods:
- Factoring
- Quadratic formula: x = (-b ± √(b²-4ac)) / 2a
- Completing the square',
'EDUCARE Mathematics Department', 'Pending'),

(1, 'Algebra Practice Exercises - Systems of Equations',
'Practice solving systems of equations:

1. Solve the system:
   x + y = 10
   x - y = 4

2. Solve the system:
   2x + 3y = 12
   x - y = 1

3. Solve the system:
   3x + 2y = 16
   2x - y = 5

Methods:
- Substitution
- Elimination
- Graphing',
'EDUCARE Mathematics Department', 'Pending');

-- Insert sample pending materials for Limits (topic_id = 2)
INSERT INTO material (topic_id, title, content, source_citation, approval_status) VALUES
(2, 'Limits Practice Exercises - Basic Limits',
'Practice evaluating limits:

1. Find the limit: lim(x→2) (x² - 4)/(x - 2)
2. Find the limit: lim(x→3) (x² - 9)/(x - 3)
3. Find the limit: lim(x→0) sin(x)/x
4. Find the limit: lim(x→∞) (3x² + 2x)/(x² - 1)
5. Find the limit: lim(x→1) (x³ - 1)/(x - 1)

Key Concepts:
- Direct substitution
- Factoring
- L''Hôpital''s Rule
- Squeeze Theorem',
'EDUCARE Mathematics Department', 'Pending'),

(2, 'Limits Practice Exercises - Continuity',
'Practice with continuity and limits:

1. Determine if f(x) = (x² - 1)/(x - 1) is continuous at x = 1
2. Find the value of k that makes f(x) continuous at x = 2:
   f(x) = {x² + 1, if x ≠ 2
           {k, if x = 2
3. Identify all points of discontinuity for f(x) = 1/(x - 3)
4. Prove that f(x) = x² is continuous everywhere
5. Find the limit: lim(x→0) |x|/x

Types of Discontinuity:
- Removable
- Jump
- Infinite',
'EDUCARE Mathematics Department', 'Pending');

-- Insert sample pending materials for Integration (topic_id = 3)
INSERT INTO material (topic_id, title, content, source_citation, approval_status) VALUES
(3, 'Integration Practice Exercises - Basic Integrals',
'Practice evaluating integrals:

1. ∫ (3x² + 2x) dx
2. ∫ sin(x) dx
3. ∫ eˣ dx
4. ∫ 1/x dx
5. ∫ (x³ - 2x + 5) dx

Integration Rules:
- Power Rule: ∫ xⁿ dx = xⁿ⁺¹/(n+1) + C
- Exponential: ∫ eˣ dx = eˣ + C
- Trigonometric: ∫ sin(x) dx = -cos(x) + C
- Logarithmic: ∫ 1/x dx = ln|x| + C',
'EDUCARE Mathematics Department', 'Pending'),

(3, 'Integration Practice Exercises - Definite Integrals',
'Practice evaluating definite integrals:

1. ∫₀² (x² + 1) dx
2. ∫₁³ (2x - 1) dx
3. ∫₀π sin(x) dx
4. ∫₋₁¹ x² dx
5. ∫₀¹ eˣ dx

Fundamental Theorem of Calculus:
∫ₐᵇ f(x) dx = F(b) - F(a)
where F is an antiderivative of f',
'EDUCARE Mathematics Department', 'Pending'),

(3, 'Integration Practice Exercises - Integration by Parts',
'Practice integration by parts:

1. ∫ x·eˣ dx
2. ∫ x·sin(x) dx
3. ∫ ln(x) dx
4. ∫ x²·cos(x) dx
5. ∫ eˣ·sin(x) dx

Integration by Parts Formula:
∫ u dv = uv - ∫ v du

Choose u using LIATE:
- Logarithmic
- Inverse trigonometric
- Algebraic
- Trigonometric
- Exponential',
'EDUCARE Mathematics Department', 'Pending');

-- Verify the inserts
SELECT 
    m.material_id,
    m.title,
    t.topic_name,
    m.approval_status,
    m.generated_date
FROM material m
JOIN topics t ON m.topic_id = t.topic_id
WHERE m.approval_status = 'Pending'
ORDER BY m.generated_date DESC;

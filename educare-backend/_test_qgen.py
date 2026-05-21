from question_generator import generate_questions

topics = ['Probability', 'Derivatives', 'Integration', 'Trigonometry', 'Sets',
          'Algebra', 'Limits', 'Coordinate Geometry', 'Matrix', 'Statistics']
for t in topics:
    qs = generate_questions(t, count=1, difficulty='medium')
    if qs:
        print('%-25s => %s' % (t, qs[0]['question'][:60]))

print('\n--- Probability questions (3) ---')
for i, q in enumerate(generate_questions('Probability', count=3, difficulty='medium'), 1):
    print('Q%d: %s' % (i, q['question'][:70]))
    for j, o in enumerate(q['options']):
        marker = ' <-- CORRECT' if j == q['correct_index'] else ''
        print('   %s. %s%s' % (chr(65+j), o, marker))

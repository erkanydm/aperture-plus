import sys
sys.path.insert(0, '/mnt/user-data/uploads')

with open('/mnt/user-data/uploads/APERTURE_COMPLETE_CODE.py', 'r') as f:
    content = f.read()

exec(compile(content, 'APERTURE_COMPLETE_CODE.py', 'exec'))

files = {
    'config.py': CONFIG_PY,
    'data_fetcher.py': DATA_FETCHER_PY,
    'scorer.py': SCORER_PY,
    'content_generator.py': CONTENT_GENERATOR_PY,
    'email_builder.py': EMAIL_BUILDER_PY,
    'social_poster.py': SOCIAL_POSTER_PY,
    'sender.py': SENDER_PY,
    'scheduler.py': SCHEDULER_PY,
}

for filename, content in files.items():
    with open(filename, 'w') as f:
        f.write(content.strip())
    print(f"Created {filename}")

with open('requirements.txt', 'w') as f:
    f.write(REQUIREMENTS.strip())

with open('.env.example', 'w') as f:
    f.write(ENV_TEMPLATE.strip())

print("\nAll files created successfully.")

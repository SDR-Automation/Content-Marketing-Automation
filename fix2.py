import pathlib
content = open('demo_content.txt', 'w', encoding='utf-8')
content.write('# Zero Trust\n\n## Summary\n\nZero Trust is foundational.\n\n## Pillar 1: Identity\n\n- MFA for all users\n- Privileged Access Management\n\n## Pillar 2: Devices\n\n- Endpoint detection on all devices\n- Device compliance policies\n\n## Conclusion\n\nZero Trust is a continuous journey.\n')
content.close()
print('demo_content.txt created')

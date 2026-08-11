from automate_announcement import compose_html


intake_result={'needs_clarification': False, 'subject': 'Important: Office Server Shutdown on November 22', 'bcc': ['adil.shaikh@sourcefuse.com', 'abcd@sourcefuse.com', 'xyz@sourcefuse.com'], 'email_content': 'Hi everyone,\n\nPlease be advised that all office servers will be completely shut off on November 22 for scheduled maintenance.\n\nDuring this period, server access and related local services will be unavailable. Please plan your work and save any critical files in advance.\n\nThank you for your cooperation.\n\nBest regards,\n\nAadil Shaikh,\n[IT Department]', 'image_placement': None, 'use_snap_as_template': True}
compose_output = compose_html(intake_result)  # intake_result = your printed output from last step
print(compose_output["email_content"])

# save + open in browser to actually see it rendered
with open("preview.html", "w", encoding="utf-8") as f:
    f.write(compose_output["email_content"])
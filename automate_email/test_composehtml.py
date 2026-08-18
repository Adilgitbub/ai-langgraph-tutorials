from automate_announcement import compose_html,auto_review,optimize


intake_result={'needs_clarification': False, 'subject': 'Important: Office Server Shutdown on November 22', 'bcc': ['adil.shaikh@sourcefuse.com', 'abcd@sourcefuse.com', 'xyz@sourcefuse.com'], 'email_content': 'Hi everyone,\n\nPlease be advised that all office servers will be completely shut off on November 22 for scheduled maintenance.\n\nDuring this period, server access and related local services will be unavailable. Please plan your work and save any critical files in advance.\n\nThank you for your cooperation.\n\nBest regards,\n\nAadil Shaikh,\n[IT Department]', 'image_placement': None, 'use_snap_as_template': True}
# compose_output = compose_html(intake_result)  # intake_result = your printed output from last step
# print(compose_output["email_content"])
autoreview_state={

"use_snap_as_template":True,
"use_snap_as_template":True,
"client_snap_path": "uploads/ff48d9d2/client_snap.png",
"html_body": "<html lang=\"en\">\n<head>\n    <meta charset=\"UTF-8\">\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n    <title>Office Server Shutdown Notice</title>\n</head>\n<body style=\"font-family: Arial, sans-serif; font-size: 14px; color: #222222; line-height: 1.5; margin: 20px;\">\n    <p>Hi everyone,</p>\n    <p>Please be advised that all office servers will be completely shut off on <span style=\"background-color:yellow\"><b style=\"color:black\">November 22</b></span> for scheduled maintenance.</p>\n    <p>During this period, server access and related local services will be unavailable. <span style=\"background-color:#B0E0E6\">Please plan your work and save any critical files in advance.</span></p>\n    <p>Thank you for your cooperation.</p>\n    <p>Best regards,<br>Aadil Shaikh,<br>[IT Department]</p>\n</body>\n</html>"
}
auto_review=auto_review(autoreview_state);
print(f"auto review response {auto_review['evaluate']} {auto_review['review_score']} {auto_review['review_feedback']}")

# save + open in browser to actually see it rendered
# with open("preview.html", "w", encoding="utf-8") as f:
#     f.write(compose_output["email_content"])

# -------- test optimize ----------
# optimize_state={
#     "iteration":0,
# "review_feedback":"Please plan your work and save any critical files in advance.' should have a cyan/light blue background highlight instead of yellow, and it should not be bold",
# "use_snap_as_template":True,
# "use_snap_as_template":True,
# "client_snap_path": "uploads/ff48d9d2/client_snap.png",
# "html_body":"<html lang=\"en\">\n<head>\n    <meta charset=\"UTF-8\">\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n    <title>Office Server Shutdown Notice</title>\n</head>\n<body style=\"font-family: Arial, sans-serif; font-size: 14px; color: #222222; line-height: 1.5; margin: 20px;\">\n    <p>Hi everyone,</p>\n    <p>Please be advised that all office servers will be completely shut off on <span style=\"background-color:yellow\"><b>November 22</b></span> for scheduled maintenance.</p>\n    <p>During this period, server access and related local services will be unavailable. <span style=\"background-color:yellow\"><b>Please plan your work and save any critical files in advance.</b></span></p>\n    <p>Thank you for your cooperation.</p>\n    <p>Best regards,<br>Aadil Shaikh,<br>[IT Department]</p>\n</body>\n</html>"
# }

# result_optimize =optimize(optimize_state)
# print(result_optimize.get('html_body'))
# print(result_optimize.get('iteration'))
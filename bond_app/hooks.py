app_name = "bond_app"
app_title = "Bond Market"
app_publisher = "Swetha Sarala"
app_description = "Bond Market and Fixed Income Management with AI Assistant"
app_email = "swethasarala1808@gmail.com"
app_license = "MIT"
app_version = "1.0.0"

after_install = "bond_app.install.after_install"

website_route_rules = [
    {"from_route": "/bond", "to_route": "bond"},
    {"from_route": "/bond-dashboard", "to_route": "bond-dashboard"},
]

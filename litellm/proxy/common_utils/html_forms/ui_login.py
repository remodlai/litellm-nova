import os

url_to_redirect_to = os.getenv("PROXY_BASE_URL", "")
server_root_path = os.getenv("SERVER_ROOT_PATH", "")
if server_root_path != "":
    url_to_redirect_to += server_root_path
url_to_redirect_to += "/login"
html_form = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Remodl AI Gateway Login</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background-color: #030c27;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            color: #333;
            overflow: hidden;
            position: relative;
        }}

        /* Animated orbital background */
        .bg-animation {{
            position: fixed;
            inset: 0;
            z-index: 1;
            pointer-events: none;
        }}

        .radial-gradient {{
            position: absolute;
            inset: 0;
            background: radial-gradient(circle at 50% 50%, rgba(0, 180, 216, 0.08), rgba(0, 0, 0, 0));
        }}

        /* Keyframe animations */
        @keyframes rotate-forward {{
            from {{ transform: rotate(0deg); }}
            to {{ transform: rotate(360deg); }}
        }}

        @keyframes rotate-backward {{
            from {{ transform: rotate(0deg); }}
            to {{ transform: rotate(-360deg); }}
        }}

        @keyframes pulse-opacity {{
            0%, 100% {{ opacity: 0.15; }}
            50% {{ opacity: 0.25; }}
        }}

        @keyframes pulse-opacity-mid {{
            0%, 100% {{ opacity: 0.2; }}
            50% {{ opacity: 0.35; }}
        }}

        @keyframes pulse-opacity-inner {{
            0%, 100% {{ opacity: 0.2; }}
            50% {{ opacity: 0.4; }}
        }}

        @keyframes pulse-node {{
            0%, 100% {{
                transform: scale(0.9);
                opacity: 0.4;
            }}
            50% {{
                transform: scale(1.1);
                opacity: 0.8;
            }}
        }}

        @keyframes pulse-center {{
            0%, 100% {{
                transform: scale(0.9);
                opacity: 0.4;
            }}
            50% {{
                transform: scale(1.05);
                opacity: 0.8;
            }}
        }}

        @keyframes pulse-wave {{
            0% {{
                transform: scale(0.5);
                opacity: 0;
            }}
            50% {{
                opacity: 0.3;
            }}
            100% {{
                transform: scale(1.8);
                opacity: 0;
            }}
        }}

        .outer-ring {{
            animation: rotate-forward 120s linear infinite, pulse-opacity 8s ease-in-out infinite;
        }}

        .middle-ring {{
            animation: rotate-backward 90s linear infinite, pulse-opacity-mid 6s ease-in-out infinite;
        }}

        .inner-ring {{
            animation: rotate-forward 60s linear infinite, pulse-opacity-inner 7s ease-in-out infinite;
        }}

        .orbital-node {{
            animation: pulse-node 6s ease-in-out infinite;
        }}

        .center-node {{
            animation: pulse-center 6s ease-in-out infinite;
        }}

        .pulse-wave {{
            animation: pulse-wave 4s ease-out infinite;
        }}

        @keyframes pulse-connection {{
            0%, 100% {{ opacity: 0.05; }}
            50% {{ opacity: 0.15; }}
        }}

        .connection-line {{
            animation: pulse-connection 5s ease-in-out infinite;
        }}

        .connection-to-center {{
            animation: pulse-connection 6s ease-in-out infinite;
        }}

        /* Form styling */
        .form-container {{
            position: relative;
            z-index: 10;
            width: 450px;
            max-width: 90%;
        }}

        form {{
            background-color: rgba(255, 255, 255, 0.98);
            backdrop-filter: blur(20px);
            padding: 48px;
            border-radius: 20px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.15);
        }}
        
        .logo-container {{
            text-align: center;
            margin-bottom: 30px;
        }}
        
        .logo {{
            font-size: 24px;
            font-weight: 600;
            color: #1e293b;
        }}
        
        h2 {{
            margin: 0 0 10px;
            color: #1e293b;
            font-size: 28px;
            font-weight: 600;
            text-align: center;
        }}
        
        .subtitle {{
            color: #64748b;
            margin: 0 0 20px;
            font-size: 16px;
            text-align: center;
        }}

        .info-box {{
            background-color: #f1f5f9;
            border-radius: 6px;
            padding: 20px;
            margin-bottom: 30px;
            border-left: 4px solid #2563eb;
        }}
        
        .info-header {{
            display: flex;
            align-items: center;
            margin-bottom: 12px;
            color: #1e40af;
            font-weight: 600;
            font-size: 16px;
        }}
        
        .info-header svg {{
            margin-right: 8px;
        }}
        
        .info-box p {{
            color: #475569;
            margin: 8px 0;
            line-height: 1.5;
            font-size: 14px;
        }}

        label {{
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            color: #334155;
            font-size: 14px;
        }}
        
        .required {{
            color: #dc2626;
            margin-left: 2px;
        }}

        input[type="text"],
        input[type="password"] {{
            width: 100%;
            padding: 10px 14px;
            margin-bottom: 20px;
            box-sizing: border-box;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            font-size: 15px;
            color: #1e293b;
            background-color: #fff;
            transition: border-color 0.2s, box-shadow 0.2s;
        }}
        
        input[type="text"]:focus,
        input[type="password"]:focus {{
            outline: none;
            border-color: #3b82f6;
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
        }}

        .toggle-password {{
            display: flex;
            align-items: center;
            margin-top: -15px;
            margin-bottom: 20px;
        }}
        
        .toggle-password input[type="checkbox"] {{
            margin-right: 8px;
            vertical-align: middle;
            width: 16px;
            height: 16px;
        }}
        
        .toggle-password label {{
            margin-bottom: 0;
            font-size: 14px;
            cursor: pointer;
            line-height: 1;
        }}

        input[type="submit"] {{
            background-color: #6466E9;
            color: #fff;
            cursor: pointer;
            font-weight: 500;
            border: none;
            padding: 10px 16px;
            transition: background-color 0.2s;
            border-radius: 6px;
            margin-top: 10px;
            font-size: 14px;
            width: 100%;
        }}

        input[type="submit"]:hover {{
            background-color: #4138C2;
        }}
        
        a {{
            color: #3b82f6;
            text-decoration: none;
        }}

        a:hover {{
            text-decoration: underline;
        }}
        
        code {{
            background-color: #f1f5f9;
            padding: 2px 4px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 13px;
            color: #334155;
        }}
        
        .help-text {{
            color: #64748b;
            font-size: 14px;
            margin-top: -12px;
            margin-bottom: 20px;
        }}
    </style>
</head>
<body>
    <!-- Animated background -->
    <div class="bg-animation">
        <div class="radial-gradient"></div>

        <svg class="orbital-svg" viewBox="0 0 1000 1000" style="position: absolute; width: 100%; height: 100%;">
            <defs>
                <radialGradient id="nodeGradient">
                    <stop offset="0%" stop-color="#00b4d8" stop-opacity="0.8" />
                    <stop offset="100%" stop-color="#00b4d8" stop-opacity="0" />
                </radialGradient>
            </defs>

            <!-- Outer ring -->
            <circle class="outer-ring" cx="500" cy="500" r="350" fill="none" stroke="rgba(0, 180, 216, 0.15)" stroke-width="0.8" />

            <!-- Middle ring -->
            <circle class="middle-ring" cx="500" cy="500" r="250" fill="none" stroke="rgba(105, 105, 179, 0.2)" stroke-width="1" />

            <!-- Inner ring -->
            <circle class="inner-ring" cx="500" cy="500" r="150" fill="none" stroke="rgba(173, 52, 62, 0.2)" stroke-width="1.2" />

            <!-- Connection lines between nodes (creating graph structure) -->
            <line class="connection-line" x1="850" y1="500" x2="500" y2="150" stroke="rgba(0, 180, 216, 0.1)" stroke-width="1" style="animation-delay: 0s;" />
            <line class="connection-line" x1="500" y1="150" x2="150" y2="500" stroke="rgba(0, 180, 216, 0.1)" stroke-width="1" style="animation-delay: 0.3s;" />
            <line class="connection-line" x1="150" y1="500" x2="500" y2="850" stroke="rgba(0, 180, 216, 0.1)" stroke-width="1" style="animation-delay: 0.6s;" />
            <line class="connection-line" x1="500" y1="850" x2="850" y2="500" stroke="rgba(0, 180, 216, 0.1)" stroke-width="1" style="animation-delay: 0.9s;" />
            <line class="connection-line" x1="750" y1="250" x2="850" y2="500" stroke="rgba(105, 105, 179, 0.1)" stroke-width="1" style="animation-delay: 1.2s;" />

            <!-- Connections to center -->
            <line class="connection-to-center" x1="850" y1="500" x2="500" y2="500" stroke="rgba(0, 180, 216, 0.08)" stroke-width="0.8" style="animation-delay: 0s;" />
            <line class="connection-to-center" x1="500" y1="150" x2="500" y2="500" stroke="rgba(0, 180, 216, 0.08)" stroke-width="0.8" style="animation-delay: 1s;" />
            <line class="connection-to-center" x1="150" y1="500" x2="500" y2="500" stroke="rgba(0, 180, 216, 0.08)" stroke-width="0.8" style="animation-delay: 2s;" />
            <line class="connection-to-center" x1="500" y1="850" x2="500" y2="500" stroke="rgba(0, 180, 216, 0.08)" stroke-width="0.8" style="animation-delay: 3s;" />
            <line class="connection-to-center" x1="750" y1="250" x2="500" y2="500" stroke="rgba(173, 52, 62, 0.08)" stroke-width="0.8" style="animation-delay: 4s;" />

            <!-- Mid-ring nodes -->
            <circle class="orbital-node" cx="750" cy="500" r="12" fill="url(#nodeGradient)" style="animation-delay: 0.5s;" />
            <circle class="orbital-node" cx="500" cy="250" r="12" fill="url(#nodeGradient)" style="animation-delay: 1.5s;" />
            <circle class="orbital-node" cx="250" cy="500" r="12" fill="url(#nodeGradient)" style="animation-delay: 2.5s;" />
            <circle class="orbital-node" cx="500" cy="750" r="12" fill="url(#nodeGradient)" style="animation-delay: 3.5s;" />

            <!-- Orbital nodes on outer ring -->
            <circle class="orbital-node" cx="850" cy="500" r="15" fill="url(#nodeGradient)" style="animation-delay: 0s;" />
            <circle class="orbital-node" cx="500" cy="150" r="15" fill="url(#nodeGradient)" style="animation-delay: 1.2s;" />
            <circle class="orbital-node" cx="150" cy="500" r="15" fill="url(#nodeGradient)" style="animation-delay: 2.4s;" />
            <circle class="orbital-node" cx="500" cy="850" r="15" fill="url(#nodeGradient)" style="animation-delay: 3.6s;" />
            <circle class="orbital-node" cx="750" cy="250" r="15" fill="url(#nodeGradient)" style="animation-delay: 4.8s;" />

            <!-- Central brain node -->
            <circle class="center-node" cx="500" cy="500" r="60" fill="none" stroke="rgba(0, 180, 216, 0.4)" stroke-width="1.5" />
            <circle cx="500" cy="500" r="10" fill="rgba(0, 180, 216, 0.6)" />

            <!-- Inner pulse -->
            <circle class="pulse-wave" cx="500" cy="500" r="40" fill="rgba(0, 180, 216, 0.08)" />
        </svg>
    </div>

    <!-- Login form -->
    <div class="form-container">
        <form action="{url_to_redirect_to}" method="post">
        <div class="logo-container">
            <div class="logo">
                <img src="https://lexiq-nova-media.s3.us-east-1.amazonaws.com/Color+logo+-+no+background.svg" alt="Remodl Logo" width="auto" height="50">
            </div>
        </div>
        <h2>Login</h2>
        <p class="subtitle">Access the Remodl AI Gateway Admin UI.</p>
        <div class="info-box">
            <div class="info-header">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="16" x2="12" y2="12"></line>
                    <line x1="12" y1="8" x2="12.01" y2="8"></line>
                </svg>
                Default Credentials
            </div>
            <p>By default, Username is <code>admin</code> and Password is your set LiteLLM Proxy <code>MASTER_KEY</code>.</p>
            <p>Need to set UI credentials or SSO? <a href="https://docs.litellm.ai/docs/proxy/ui" target="_blank">Check the documentation</a>.</p>
        </div>
        <label for="username">Username<span class="required">*</span></label>
        <input type="text" id="username" name="username" required placeholder="Enter your username" autocomplete="username">
        
        <label for="password">Password<span class="required">*</span></label>
        <input type="password" id="password" name="password" required placeholder="Enter your password" autocomplete="current-password">
        <div class="toggle-password">
            <input type="checkbox" id="show-password" onclick="togglePasswordVisibility()">
            <label for="show-password">Show password</label>
        </div>
            <input type="submit" value="Login">
        </form>
    </div>

    <script>
        function togglePasswordVisibility() {{
            var passwordField = document.getElementById("password");
            passwordField.type = passwordField.type === "password" ? "text" : "password";
        }}

        // Create floating particles
        function createParticles() {{
            const bgAnimation = document.querySelector('.bg-animation');
            for (let i = 0; i < 20; i++) {{
                const particle = document.createElement('div');
                particle.className = 'particle';
                particle.style.left = Math.random() * 100 + '%';
                particle.style.top = Math.random() * 100 + '%';
                particle.style.animationDuration = (10 + Math.random() * 20) + 's';
                particle.style.animationDelay = Math.random() * 5 + 's';
                bgAnimation.appendChild(particle);
            }}
        }}

        createParticles();
    </script>
    <style>
        .particle {{
            position: absolute;
            width: 2px;
            height: 2px;
            background: #00b4d8;
            border-radius: 50%;
            animation: float-particle 15s linear infinite;
        }}

        @keyframes float-particle {{
            0% {{
                transform: translate(0, 0);
                opacity: 0;
            }}
            50% {{
                opacity: 0.6;
            }}
            100% {{
                transform: translate(calc((100vw - 100%) * (var(--random-x, 0.5) - 0.5)), calc((100vh - 100%) * (var(--random-y, 0.5) - 0.5)));
                opacity: 0;
            }}
        }}
    </style>
</body>
</html>
"""

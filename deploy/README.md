# Deployment Notes

1. Copy the files in this folder to the server:
   - `arb-bot.service` → `/etc/systemd/system/arb-bot.service`
   - `deploy.sh` → `/opt/arb-bot/deploy.sh`
2. Adjust values before enabling:
   - Replace `User=deploy` and `Group=deploy` with the account that should run the service.
   - Update the port in `ExecStart` if you expose the API on a different port.
3. On the server run:
   ```bash
   sudo cp /opt/arb-bot/deploy/arb-bot.service /etc/systemd/system/arb-bot.service
   sudo chmod 644 /etc/systemd/system/arb-bot.service
   sudo cp /opt/arb-bot/deploy/deploy.sh /opt/arb-bot/deploy.sh
   sudo chmod +x /opt/arb-bot/deploy.sh
   sudo systemctl daemon-reload
   sudo systemctl enable --now arb-bot.service
   ```
4. To deploy new changes later execute:
   ```bash
   /opt/arb-bot/deploy.sh
   ```
   The script pulls the latest code, installs dependencies, runs Alembic migrations and restarts the service.
   5. Ensure the deploy user has passwordless sudo for `systemctl restart arb-bot.service`, or adjust the script to prompt for a password.

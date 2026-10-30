// PM2 sozlamasi: VPS'da `pm2 start ecosystem.config.js`
// Port: sizga ajratilgan 3200–3299 oralig'idan bo'sh bittasini tanlang.
module.exports = {
  apps: [
    {
      name: "face-attendance",
      cwd: __dirname,
      script: "venv/bin/uvicorn",
      args: "api:app --host 127.0.0.1 --port 3250 --workers 1",
      interpreter: "none",
      max_memory_restart: "500M",
    },
  ],
};

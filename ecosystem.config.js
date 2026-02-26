module.exports = {
    apps: [{
        name: 'n8nhttp',
        script: '/home/alaadin/n8nhttp/start.sh',
        cwd: '/home/alaadin/n8nhttp',
        interpreter: '/bin/bash',
        watch: false,
        autorestart: true,
        max_restarts: 10,
        restart_delay: 5000,
        env: {
            NODE_ENV: 'production'
        }
    }]
};

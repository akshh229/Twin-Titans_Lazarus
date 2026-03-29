const fs = require('fs');
const path = require('path');

const basePath = 'E:\\Project Lazarus';
const directories = [
    'nginx',
    'backend\\app\\models',
    'backend\\app\\schemas',
    'backend\\app\\api',
    'backend\\app\\websocket',
    'backend\\app\\services',
    'backend\\app\\utils',
    'backend\\app\\workers',
    'backend\\tests',
    'backend\\migrations\\versions',
    'backend\\seed_data',
    'frontend\\src\\api',
    'frontend\\src\\components',
    'frontend\\src\\pages',
    'frontend\\src\\hooks',
    'frontend\\src\\types',
    'frontend\\src\\styles',
    'frontend\\public'
];

directories.forEach(dir => {
    const fullPath = path.join(basePath, dir);
    if (!fs.existsSync(fullPath)) {
        fs.mkdirSync(fullPath, { recursive: true });
        console.log(`Created: ${dir}`);
    }
});

console.log('\nAll directories created successfully!');

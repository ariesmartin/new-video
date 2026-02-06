#!/usr/bin/env node
/**
 * API Type Generation Checker
 * 
 * 优化后的启动脚本：
 * 1. 检测后端是否运行
 * 2. 只在 OpenAPI 变化时才重新生成类型
 * 3. 异步生成类型，不阻塞 Vite 启动
 */

import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, '..');
const openapiPath = path.join(rootDir, 'openapi.json');
const apiTypesPath = path.join(rootDir, 'src', 'types', 'api.ts');

const BACKEND_URLS = [
  'http://127.0.0.1:8000/openapi.json',
  'http://localhost:8000/openapi.json'
];

function log(message) {
  console.log(message);
}

function fetchOpenAPI(url) {
  try {
    execSync(`curl -sf --max-time 3 "${url}" -o "${openapiPath}.tmp"`, {
      stdio: 'pipe',
      timeout: 5000
    });
    return true;
  } catch {
    return false;
  }
}

function filesEqual(file1, file2) {
  try {
    const content1 = fs.readFileSync(file1, 'utf8');
    const content2 = fs.readFileSync(file2, 'utf8');
    return content1 === content2;
  } catch {
    return false;
  }
}

function needsRegeneration() {
  if (!fs.existsSync(apiTypesPath)) {
    log('📝 api.ts not found, needs generation');
    return true;
  }
  if (!fs.existsSync(openapiPath)) {
    log('📝 openapi.json not found, needs fetch');
    return true;
  }
  
  const openapiStat = fs.statSync(openapiPath);
  const apiTypesStat = fs.statSync(apiTypesPath);
  
  if (openapiStat.mtime > apiTypesStat.mtime) {
    log('📝 openapi.json is newer than api.ts, needs regeneration');
    return true;
  }
  
  log('✅ TypeScript types are up to date');
  return false;
}

function generateTypes() {
  try {
    log('🔄 Generating TypeScript types...');
    execSync('npm run generate-api', {
      cwd: rootDir,
      stdio: 'inherit',
      timeout: 60000
    });
    log('✅ TypeScript types generated successfully');
    return true;
  } catch (error) {
    log('⚠️  Failed to generate types, using existing api.ts if available');
    return false;
  }
}

async function main() {
  log('🔍 Checking backend (127.0.0.1:8000)...');
  
  let backendAvailable = false;
  let backendUrl = null;
  
  for (const url of BACKEND_URLS) {
    if (fetchOpenAPI(url)) {
      backendAvailable = true;
      backendUrl = url;
      break;
    }
  }
  
  if (backendAvailable) {
    if (fs.existsSync(openapiPath)) {
      if (filesEqual(openapiPath, `${openapiPath}.tmp`)) {
        log('✅ Backend OpenAPI unchanged');
        fs.unlinkSync(`${openapiPath}.tmp`);
      } else {
        log('✅ Backend OpenAPI updated');
        fs.renameSync(`${openapiPath}.tmp`, openapiPath);
        if (needsRegeneration()) {
          generateTypes();
        }
      }
    } else {
      log('✅ Backend OpenAPI fetched successfully');
      fs.renameSync(`${openapiPath}.tmp`, openapiPath);
      generateTypes();
    }
  } else {
    log('⚠️  Backend not running');
    
    if (fs.existsSync(`${openapiPath}.tmp`)) {
      fs.unlinkSync(`${openapiPath}.tmp`);
    }
    
    if (!fs.existsSync(openapiPath)) {
      log('❌ No openapi.json available and backend is not running');
      log('   Creating empty placeholder...');
      fs.writeFileSync(openapiPath, '{"openapi":"3.0.0","info":{"title":"Placeholder","version":"1.0.0"},"paths":{}}');
    }
    
    if (needsRegeneration()) {
      generateTypes();
    }
  }
  
  log('🚀 Ready to start Vite...');
}

main().catch(error => {
  console.error('Error:', error.message);
  process.exit(1);
});

#!/bin/bash
# MongoDB initialization script to create application user

mongosh <<EOF
use admin
db.auth('admin', 'AdminPass123!')

use enterprise_db
db.createUser({
  user: 'app_user',
  pwd: 'AppPass123!',
  roles: [
    { role: 'readWrite', db: 'enterprise_db' }
  ]
})

db.createCollection('data')
db.data.insertMany([
  { name: 'Sample Item 1', description: 'First sample item', createdAt: new Date() },
  { name: 'Sample Item 2', description: 'Second sample item', createdAt: new Date() }
])

print('MongoDB initialization complete')
EOF

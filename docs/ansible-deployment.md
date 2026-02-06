# Ansible Deployment Guide

## Overview

This guide covers deploying the Enterprise Platform using Ansible on RHEL 8/9 family operating systems.

## Supported Operating Systems

| OS Family | Distributions | Status |
|-----------|--------------|--------|
| **RHEL 8** | RHEL 8, AlmaLinux 8, Rocky Linux 8 | ✅ Tested |
| **RHEL 9** | RHEL 9, AlmaLinux 9, Rocky Linux 9 | ✅ Tested |

---

## Prerequisites

### Control Node Requirements

- Ansible 2.15 or higher
- Python 3.8+
- SSH access to target hosts
- Sudo privileges on target hosts

### Target Host Requirements

- RHEL 8/9, AlmaLinux 8/9, or Rocky Linux 8/9
- Python 3 installed
- SSH server running
- Sudo access for deployment user

---

## Installation

### 1. Install Ansible

```bash
# On RHEL/AlmaLinux/Rocky Linux
sudo dnf install ansible-core

# Verify installation
ansible --version
```

### 2. Clone Repository

```bash
git clone https://github.com/yourusername/enterprise-platform-rhel-k8s.git
cd enterprise-platform-rhel-k8s/ansible
```

### 3. Configure Inventory

Edit `inventory/hosts.yml` with your server details:

```yaml
all:
  children:
    rhel9_family:
      children:
        rhel9:
          hosts:
            rhel9-server-01:
              ansible_host: 192.168.1.20
              ansible_user: ansible
```

### 4. Test Connectivity

```bash
ansible all -i inventory/hosts.yml -m ping
```

---

## Configuration

### Group Variables

#### All Hosts (`group_vars/all.yml`)

```yaml
app_name: enterprise_platform
app_version: "1.0.0"
mariadb_version: "10.11"
mongodb_version: "7.0"
firewall_enabled: true
selinux_state: enforcing
```

#### RHEL 8 Specific (`group_vars/rhel8_family.yml`)

```yaml
os_family: "rhel8"
python_package: python38
mariadb_repo_baseurl: "http://yum.mariadb.org/10.11/rhel8-amd64"
```

#### RHEL 9 Specific (`group_vars/rhel9_family.yml`)

```yaml
os_family: "rhel9"
python_package: python3
mariadb_repo_baseurl: "http://yum.mariadb.org/10.11/rhel9-amd64"
```

---

## Deployment

### Full Stack Deployment

```bash
cd ansible
ansible-playbook -i inventory/hosts.yml playbooks/site.yml
```

### Component-Specific Deployment

#### MariaDB Only

```bash
ansible-playbook -i inventory/hosts.yml playbooks/mariadb.yml
```

#### MongoDB Only

```bash
ansible-playbook -i inventory/hosts.yml playbooks/mongodb.yml
```

#### Application Only

```bash
ansible-playbook -i inventory/hosts.yml playbooks/application.yml
```

---

## RHEL 8/9 Compatibility

### Conditional Logic

The playbooks automatically detect the OS version and apply appropriate configurations:

```yaml
- name: Detect OS version
  set_fact:
    is_rhel8: "{{ ansible_distribution_major_version == '8' }}"
    is_rhel9: "{{ ansible_distribution_major_version == '9' }}"

- name: Install package (RHEL 8)
  package:
    name: python38
  when: is_rhel8

- name: Install package (RHEL 9)
  package:
    name: python3
  when: is_rhel9
```

### Key Differences

| Component | RHEL 8 | RHEL 9 |
|-----------|--------|--------|
| Python | python38 | python3 |
| SELinux Utils | policycoreutils-python-utils | python3-policycoreutils |
| Repository URLs | rhel8-amd64 | rhel9-amd64 |

---

## Verification

### Check Service Status

```bash
# On target hosts
systemctl status mariadb
systemctl status mongod
systemctl status webapp
```

### Verify Database Connectivity

```bash
# MariaDB
mysql -u app_user -p -h localhost enterprise_db

# MongoDB
mongosh -u app_user -p enterprise_db
```

### Test Application

```bash
curl http://localhost:8080/health
```

---

## Troubleshooting

### Issue: Python Not Found

```bash
# Install Python on target host
sudo dnf install python3

# Verify
python3 --version
```

### Issue: Repository Not Found

```bash
# Clear cache
sudo dnf clean all

# Rebuild cache
sudo dnf makecache
```

### Issue: Firewall Blocking Connections

```bash
# Check firewall rules
sudo firewall-cmd --list-all

# Add service
sudo firewall-cmd --permanent --add-service=mysql
sudo firewall-cmd --reload
```

---

## Advanced Usage

### Using Ansible Vault for Secrets

```bash
# Create vault file
ansible-vault create group_vars/vault.yml

# Add encrypted variables
mariadb_root_password: "SecurePassword123!"
mongodb_admin_password: "SecurePassword123!"

# Run playbook with vault
ansible-playbook -i inventory/hosts.yml playbooks/site.yml --ask-vault-pass
```

### Limiting Execution to Specific Hosts

```bash
# Deploy only to RHEL 9 hosts
ansible-playbook -i inventory/hosts.yml playbooks/site.yml --limit rhel9_family

# Deploy to single host
ansible-playbook -i inventory/hosts.yml playbooks/site.yml --limit rhel9-server-01
```

### Dry Run (Check Mode)

```bash
ansible-playbook -i inventory/hosts.yml playbooks/site.yml --check
```

---

## Best Practices

1. **Use Ansible Vault** for sensitive data
2. **Test in staging** before production
3. **Use tags** for selective execution
4. **Keep playbooks idempotent**
5. **Document custom variables**
6. **Version control** all configurations
7. **Use roles** for reusability

---

## Maintenance

### Updating Packages

```bash
ansible all -i inventory/hosts.yml -m dnf -a "name=* state=latest" --become
```

### Restarting Services

```bash
ansible mariadb_servers -i inventory/hosts.yml -m systemd -a "name=mariadb state=restarted" --become
```

### Gathering Facts

```bash
ansible all -i inventory/hosts.yml -m setup
```

---

## Uninstallation

```bash
# Stop services
ansible all -i inventory/hosts.yml -m systemd -a "name=webapp state=stopped enabled=no" --become
ansible mariadb_servers -i inventory/hosts.yml -m systemd -a "name=mariadb state=stopped enabled=no" --become
ansible mongodb_servers -i inventory/hosts.yml -m systemd -a "name=mongod state=stopped enabled=no" --become

# Remove packages
ansible all -i inventory/hosts.yml -m dnf -a "name=MariaDB-server,mongodb-org state=absent" --become
```

---

## Additional Resources

- [Ansible Documentation](https://docs.ansible.com/)
- [RHEL 9 Release Notes](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/9)
- [AlmaLinux Documentation](https://wiki.almalinux.org/)
- [Rocky Linux Documentation](https://docs.rockylinux.org/)

function openAddUser() {
    document.getElementById('addUserModal').classList.add('show');
}

function openEditUser(id, name, email, role) {
    document.getElementById('editUserId').value = id;
    document.getElementById('editName').value = name;
    document.getElementById('editEmail').value = email;
    document.getElementById('editRole').value = role;
    document.getElementById('editUserModal').classList.add('show');
}

function closeModal() {
    document.querySelectorAll('.modal').forEach(m => m.classList.remove('show'));
}
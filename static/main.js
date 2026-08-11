document.addEventListener('DOMContentLoaded', () => {
  const openFolders = JSON.parse(localStorage.getItem('wiki_open_folders') || '[]');

  document.querySelectorAll('.folder-node').forEach((node, index) => {
    node.dataset.folderId = index;

    if (openFolders.includes(index.toString())) {
      node.classList.remove('collapsed');
      node.classList.add('expanded');
    }
  });

  const currentPath = window.location.pathname;
  const activeLink = document.querySelector(`.file-node a[href="${decodeURIComponent(currentPath)}"]`);

  if (activeLink) {
    activeLink.classList.add('active-page');

    let parent = activeLink.closest('.folder-node');
    while (parent) {
      parent.classList.remove('collapsed');
      parent.classList.add('expanded');

      const folderId = parent.dataset.folderId;
      if (folderId && !openFolders.includes(folderId)) {
        openFolders.push(folderId);
      }
      parent = parent.parentElement ? parent.parentElement.closest('.folder-node') : null;
    }
    localStorage.setItem('wiki_open_folders', JSON.stringify(openFolders));
  }

  document.querySelectorAll('.folder-title').forEach(title => {
    title.addEventListener('click', (e) => {
      e.stopPropagation();
      const folderNode = e.target.parentElement;
      const folderId = folderNode.dataset.folderId;

      folderNode.classList.toggle('collapsed');
      folderNode.classList.toggle('expanded');

      let currentOpen = JSON.parse(localStorage.getItem('wiki_open_folders') || '[]');
      if (folderNode.classList.contains('expanded')) {
        if (!currentOpen.includes(folderId)) currentOpen.push(folderId);
      } else {
        currentOpen = currentOpen.filter(id => id !== folderId);
      }
      localStorage.setItem('wiki_open_folders', JSON.stringify(currentOpen));
    });
  });
});
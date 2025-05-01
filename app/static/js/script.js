window.addEventListener("popstate", (event) => {
  history.pushState(null, null, window.location.href);
  window.location.replace("/login");
});

document.addEventListener('DOMContentLoaded', () => {
  history.pushState(null, null, window.location.href);
  
  user = sessionStorage.getItem('user') ? JSON.parse(sessionStorage.getItem('user')) : null;

  // Authentication check
  if (user == null) {
    window.location.replace("/login");
    return;
  }

  // Elements
  const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
  const closeSidebarButton = document.getElementById('close-sidebar');
  const sidebar = document.getElementById('sidebar');
  const checkInButton = document.getElementById('check-in-button');
  const checkInsList = document.getElementById('check-ins-list');
  const logoutButton = document.getElementById('logout-button');
  const dialogContainer = document.getElementById('dialog-container');
  
  // State
  let map;
  let currentPosition = null;
  let checkIns = [];
  let markers = [];
  let customIcon;
  let activeActionsMenu = null;

  // Initialize map
  function initMap() {
    // Create map
    map = L.map('map', { attributionControl: false }).setView([55.751244, 37.618423], 13);

    L.control.attribution({prefix: false, position: 'bottomleft'}).addTo(map); // Убирает "Leaflet"
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors'
    }).addTo(map);
    
    // Create custom icon
    customIcon = L.icon({
      iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
      iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
      shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
      iconSize: [25, 41],
      iconAnchor: [12, 41],
      popupAnchor: [1, -34],
      shadowSize: [41, 41]
    });
    
    // Add click event to map
    map.on('click', (e) => {
      setCurrentPosition(e.latlng.lat, e.latlng.lng);
    });
    
    // Find user location
    map.locate({ setView: true, maxZoom: 16 });
    
    // Handle location found
    map.on('locationfound', (e) => {
      setCurrentPosition(e.latlng.lat, e.latlng.lng);
    });
    
    // Handle location error
    map.on('locationerror', () => {
      showToast('Ошибка определения местоположения', 'Пожалуйста, разрешите доступ к геолокации', 'error');
    });
  }
  
  // Set current position and update marker
  function setCurrentPosition(lat, lng) {
    currentPosition = { lat, lng };
    
    // Remove existing selection marker
    if (markers.selectionMarker) {
      map.removeLayer(markers.selectionMarker);
    }
    
    // Add new selection marker
    markers.selectionMarker = L.marker([lat, lng], { icon: customIcon }).addTo(map);
    markers.selectionMarker.bindPopup('Локация для check-in').openPopup();
  }
  
  // Custom SweetAlert configuration for mobile - improved for z-index handling
  function showMobileFriendlyDialog(options) {
    // Close sidebar on mobile before showing dialog
    if (window.innerWidth <= 768 && sidebar.classList.contains('open')) {
      sidebar.classList.remove('open');
      mobileMenuToggle.querySelector('i').className = 'fas fa-bars';
      checkInButton.style.display = 'flex';
    }
    
    // Make dialog container capture pointer events during dialog display
    dialogContainer.style.pointerEvents = 'auto';
    
    // Set up defaults for mobile-friendly dialogs
    const defaultOptions = {
      target: dialogContainer,
      backdrop: true,
      position: 'center',
      didOpen: () => {
        // Ensure the dialog is visible and interactive
        const swalContainer = document.querySelector('.swal2-container');
        if (swalContainer) {
          swalContainer.style.pointerEvents = 'auto';
        }
      },
      didClose: () => {
        // Reset dialog container to not capture pointer events once dialog is closed
        dialogContainer.style.pointerEvents = 'none';
      }
    };
    
    // Merge with provided options
    const mergedOptions = { ...defaultOptions, ...options };
    
    return Swal.fire(mergedOptions);
  }
  
  // Handle check-in
  function handleCheckIn() {
    if (!currentPosition) {
      showToast('Не выбрана локация', 'Пожалуйста, выберите точку на карте', 'error');
      return;
    }
    
    showMobileFriendlyDialog({
      title: 'Добавить новый check-in',
      html: `
        <div class="swal2-input-container">
          <input id="swal-input-title" class="swal2-input" placeholder="Название места (например, Кафе)" value="">
        </div>
      `,
      showCancelButton: true,
      confirmButtonText: 'Сохранить',
      cancelButtonText: 'Отмена',
      focusConfirm: false,
      preConfirm: () => {
        return {
          title: document.getElementById('swal-input-title').value || 'Без названия'
        };
      }
    }).then((result) => {
      if (result.isConfirmed) {
        saveCheckIn(result.value.title);
      }
    });
  }

  // Save check-in with title
  function saveCheckIn(title) {
    var marker_id = 0;

    var newCheckIn = {
      id: 0,
      lat: currentPosition.lat,
      lng: currentPosition.lng,
      timestamp: new Date(),
      user: user.name || 'Anonymous',
      title: title
    };

      fetch('/add_marker', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + user.token
        },
        body: JSON.stringify({
          latitude: newCheckIn.lat,
          longitude: newCheckIn.lng,
          title: newCheckIn.title,
          date_time: newCheckIn.timestamp
        })
      })
      .then(response => response.json())
      .then(data => {
        if (data.error) {
          console.error('Ошибка:', data.error);
          return;
        } else {
          console.log('Маркер создан:', data);
          marker_id = data.marker_id;
          newCheckIn = {
            id: marker_id,
            lat: currentPosition.lat,
            lng: currentPosition.lng,
            timestamp: new Date(),
            user: user.name || 'Anonymous',
            title: title
          };
        
        checkIns.push(newCheckIn);
        
        // Add marker to map
        const marker = L.marker([newCheckIn.lat, newCheckIn.lng], { icon: customIcon }).addTo(map);
        markers[newCheckIn.id] = marker;
        
        marker.bindPopup(`
          <div>
            <div><strong>${newCheckIn.title}</strong></div>
            <div><strong>Пользователь:</strong> ${newCheckIn.user}</div>
            <div><strong>Время:</strong> ${formatTime(newCheckIn.timestamp)}</div>
            <div><strong>Координаты:</strong> ${newCheckIn.lat.toFixed(4)}, ${newCheckIn.lng.toFixed(4)}</div>
          </div>
        `);
        
        // Add check-in to list
        updateCheckInsList();
        
        // Show success toast
        showToast(
          'Check-in выполнен успешно',
          `${newCheckIn.title}: ${newCheckIn.lat.toFixed(4)}, ${newCheckIn.lng.toFixed(4)}`,
          'success'
        );
        
        // Close sidebar on mobile after check-in
        if (window.innerWidth <= 768) {
          sidebar.classList.remove('open');
          mobileMenuToggle.querySelector('i').className = 'fas fa-bars';
          checkInButton.style.display = 'flex';
        }
      }
    })
    .catch(error => {
      console.error('Ошибка сети:', error)
      return;
    });
  }
  
  // Update check-ins list
  function updateCheckInsList() {
    // Clear list
    checkInsList.innerHTML = '';

    fetch('/get_markers', {
      method: 'GET',
      headers: {
        'Authorization': 'Bearer ' + user.token
      }
    })
    .then(response => response.json())
    .then(data => {
      if (data.error) {
        console.error('Ошибка:', data.error);
      } else {
        console.log('Маркеры получены:', data);

        data.markers.forEach(markerData => {
          const checkIn = {
            id: markerData.id,
            lat: markerData.latitude,
            lng: markerData.longitude,
            title: markerData.title || 'Без названия',
            user: user.name || 'Anonymous',
            timestamp: new Date(markerData.date_time)
          };

          const isDuplicate = checkIns.some(item => item.id === checkIn.id);
          if (isDuplicate) return;

          const marker = L.marker([checkIn.lat, checkIn.lng], { icon: customIcon }).addTo(map);
          markers[checkIn.id] = marker;

          marker.bindPopup(`
            <div class="marker-popup">
              <div><strong>${checkIn.title}</strong></div>
              <div><strong>Пользователь:</strong> ${checkIn.user}</div>
              <div><strong>Время:</strong> ${formatTime(checkIn.timestamp)}</div>
              <div><strong>Координаты:</strong> 
                ${checkIn.lat.toFixed(4)}, ${checkIn.lng.toFixed(4)}
              </div>
            </div>
          `);

          checkIns.push(checkIn);
        });

        // Show empty state if no check-ins
        if (checkIns.length === 0) {
          checkInsList.innerHTML = `
            <div class="empty-state">
              <i class="fas fa-map-marker-alt"></i>
              <p>Нет отмеченных точек</p>
              <p class="small-text">Нажмите на карту и затем на кнопку Check-in</p>
            </div>
          `;
          return;
        }

        // Add check-ins to list
        checkIns
          .slice()
          .reverse()
          .forEach(checkIn => {
            const checkInElement = document.createElement('div');
            checkInElement.className = 'check-in-item';
            checkInElement.dataset.id = checkIn.id;

            // Main content
            checkInElement.innerHTML = `
              <div class="check-in-actions">
                <button class="check-in-actions-button">
                  <i class="fas fa-ellipsis-h"></i>
                </button>
                <div class="check-in-actions-menu">
                  <div class="check-in-action-item edit">
                    <i class="fas fa-edit"></i>
                    <span>Редактировать</span>
                  </div>
                  <div class="check-in-action-item delete">
                    <i class="fas fa-trash"></i>
                    <span>Удалить</span>
                  </div>
                </div>
              </div>
              <p class="title">
                <i class="fas fa-map-marker-alt"></i>
                <span>${checkIn.title || 'Без названия'}</span>
              </p>
              <p class="user">
                <i class="fas fa-user"></i>
                <span>${checkIn.user}</span>
              </p>
              <p class="coordinates">
                <i class="fas fa-map-pin"></i>
                <span>${checkIn.lat.toFixed(4)}, ${checkIn.lng.toFixed(4)}</span>
              </p>
              <p class="timestamp">
                <i class="fas fa-clock"></i>
                <span>${formatTime(checkIn.timestamp)}</span>
              </p>
            `;

            checkInsList.appendChild(checkInElement);

            // Add event listeners for actions
            const actionsButton = checkInElement.querySelector('.check-in-actions-button');
            const actionsMenu = checkInElement.querySelector('.check-in-actions-menu');
            const editAction = checkInElement.querySelector('.check-in-action-item.edit');
            const deleteAction = checkInElement.querySelector('.check-in-action-item.delete');

            // Toggle actions menu
            actionsButton.addEventListener('click', (e) => {
              e.stopPropagation();

              // Close any other open menus
              if (activeActionsMenu && activeActionsMenu !== actionsMenu) {
                activeActionsMenu.classList.remove('show');
              }

              actionsMenu.classList.toggle('show');

              if (actionsMenu.classList.contains('show')) {
                activeActionsMenu = actionsMenu;
              } else {
                activeActionsMenu = null;
              }
            });

            // Edit action
            editAction.addEventListener('click', () => {
              actionsMenu.classList.remove('show');
              editCheckIn(checkIn.id);
            });

            // Delete action
            deleteAction.addEventListener('click', () => {
              actionsMenu.classList.remove('show');
              deleteCheckIn(checkIn.id);
            });
          });
        }
    })
    .catch(error => console.error('Ошибка сети:', error));
  }
  
  // Edit check-in
  function editCheckIn(id) {
    const checkIn = checkIns.find(item => item.id === id);
    if (!checkIn) return;
    
    showMobileFriendlyDialog({
      title: 'Редактировать check-in',
      html: `
        <div class="swal2-input-container">
          <input id="swal-input-title" class="swal2-input" placeholder="Название места" value="${checkIn.title || ''}">
        </div>
        <div class="swal2-input-container">
          <input id="swal-input-lat" class="swal2-input" placeholder="Широта" value="${checkIn.lat}">
        </div>
        <div class="swal2-input-container">
          <input id="swal-input-lng" class="swal2-input" placeholder="Долгота" value="${checkIn.lng}">
        </div>
      `,
      showCancelButton: true,
      confirmButtonText: 'Сохранить',
      cancelButtonText: 'Отмена',
      focusConfirm: false,
      preConfirm: () => {
        const lat = parseFloat(document.getElementById('swal-input-lat').value);
        const lng = parseFloat(document.getElementById('swal-input-lng').value);
        
        if (isNaN(lat) || isNaN(lng)) {
          Swal.showValidationMessage('Пожалуйста, введите корректные координаты');
          return false;
        }
        
        return {
          title: document.getElementById('swal-input-title').value || 'Без названия',
          lat,
          lng
        };
      }
    }).then((result) => {
      if (result.isConfirmed) {
        fetch('/edit_marker', {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + user.token
          },
          body: JSON.stringify({
            marker_id: id,
            latitude: result.value.lat,
            longitude: result.value.lng,
            title: result.value.title
          })
        })
        .then(response => response.json())
        .then(data => {
          if (data.error) {
            console.error('Ошибка:', data.error);
          } else {
            console.log('Маркер изменен:', data);
            
            checkIn.title = result.value.title;
            checkIn.lat = result.value.lat;
            checkIn.lng = result.value.lng;
      
            if (markers[checkIn.id]) {
              map.removeLayer(markers[checkIn.id]);
            }
      
            const marker = L.marker([checkIn.lat, checkIn.lng], { icon: customIcon }).addTo(map);
            markers[checkIn.id] = marker;
      
            marker.bindPopup(`
              <div>
                <div><strong>${checkIn.title}</strong></div>
                <div><strong>Пользователь:</strong> ${checkIn.user}</div>
                <div><strong>Время:</strong> ${formatTime(checkIn.timestamp)}</div>
                <div><strong>Координаты:</strong> ${checkIn.lat.toFixed(4)}, ${checkIn.lng.toFixed(4)}</div>
              </div>
            `);
      
            updateCheckInsList();
            
            // Show success toast
            showToast('Check-in обновлен', `${checkIn.title} успешно обновлен`, 'success');
          }
        })
        .catch(error => console.error('Ошибка сети:', error));
      }
    });
  }
  
  // Delete check-in
  function deleteCheckIn(id) {
    const checkIn = checkIns.find(item => item.id === id);
    if (!checkIn) return;
    
    showMobileFriendlyDialog({
      title: 'Удалить check-in?',
      text: `Вы уверены, что хотите удалить "${checkIn.title || 'Без названия'}"?`,
      icon: 'warning',
      showCancelButton: true,
      confirmButtonText: 'Удалить',
      cancelButtonText: 'Отмена',
      confirmButtonColor: '#ef4444',
    }).then((result) => {
      if (result.isConfirmed) {
        console.log(id);
        fetch(`/delete_marker?marker_id=${id}`, {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + user.token
          }
        })
        .then(response => response.json())
        .then(data => {
          if (data.error) {
            console.error('Ошибка:', data.error);
            return;
          } else {
            console.log('Маркер удален:', data);
      
            if (markers[checkIn.id]) {
              map.removeLayer(markers[checkIn.id]);
              delete markers[checkIn.id];
            }
      
            checkIns = checkIns.filter(item => item.id !== id);
      
            updateCheckInsList();

            // Show success toast
            showToast('Check-in удален', 'Точка успешно удалена', 'success');
              }
            })
        .catch(error => {
          console.error('Ошибка сети:', error)
          return;
        });
      }
    });
  }
  
  // Format timestamp
  function formatTime(date) {
    return new Intl.DateTimeFormat('ru-RU', {
      hour: '2-digit',
      minute: '2-digit',
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    }).format(date);
  }
  
  // Show toast notification
  function showToast(title, description, type = 'success') {
    const toastContainer = document.getElementById('toast-container');
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    // Truncate description if too long on mobile
    let displayDescription = description;
    if (window.innerWidth <= 768 && description.length > 50) {
      displayDescription = description.substring(0, 50) + '...';
    }
    
    toast.innerHTML = `
      <div class="toast-icon">
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
      </div>
      <div class="toast-content">
        <div class="toast-title">${title}</div>
        <div class="toast-description">${displayDescription}</div>
      </div>
    `;
    
    toastContainer.appendChild(toast);
    
    // Remove toast after 3 seconds
    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => {
        toast.remove();
      }, 300);
    }, 3000);
  }
  
  // Handle logout
  function handleLogout() {
    user = null;
    sessionStorage.removeItem('user');
    window.location.href = '/login';
  }
  
  // Close active dropdown when clicking outside
  document.addEventListener('click', () => {
    if (activeActionsMenu) {
      activeActionsMenu.classList.remove('show');
      activeActionsMenu = null;
    }
  });
  
  // Event listeners
  mobileMenuToggle.addEventListener('click', () => {
    sidebar.classList.toggle('open');
    
    // Toggle icon
    const icon = mobileMenuToggle.querySelector('i');
    if (sidebar.classList.contains('open')) {
      icon.className = 'fas fa-times';
      checkInButton.style.display = 'none'; // Hide check-in button when sidebar is open
    } else {
      icon.className = 'fas fa-bars';
      checkInButton.style.display = 'flex'; // Show check-in button when sidebar is closed
    }
  });
  
  closeSidebarButton.addEventListener('click', () => {
    sidebar.classList.remove('open');
    mobileMenuToggle.querySelector('i').className = 'fas fa-bars';
    checkInButton.style.display = 'flex'; // Show check-in button when sidebar is closed
  });
  
  checkInButton.addEventListener('click', handleCheckIn);
  logoutButton.addEventListener('click', handleLogout);
  
  // Responsive adjustments
  function handleResize() {
    if (window.innerWidth <= 768) {
      // Mobile
      if (sidebar.classList.contains('open')) {
        checkInButton.style.display = 'none';
      } else {
        checkInButton.style.display = 'flex';
      }
    } else {
      // Desktop
      checkInButton.style.display = 'flex';
    }
  }
  
  window.addEventListener('resize', handleResize);
  
  // Initialize
  initMap();
  updateCheckInsList();
  handleResize();
});
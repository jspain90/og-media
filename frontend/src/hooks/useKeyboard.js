import { useEffect } from 'react';

/**
 * Hook for TV remote-style keyboard controls
 *
 * @param {Object} handlers - Object with handler functions
 * @param {Function} handlers.onLeft - Called when Left arrow is pressed (open menu)
 * @param {Function} handlers.onRight - Called when Right arrow is pressed (skip)
 * @param {Function} handlers.onSpace - Called when Space is pressed (play/pause)
 * @param {Function} handlers.onEnter - Called when Enter is pressed (fullscreen)
 * @param {boolean} handlers.menuOpen - Whether the menu is currently open
 */
export function useKeyboard({ onLeft, onRight, onSpace, onEnter, menuOpen }) {
  useEffect(() => {
    const handleKeyDown = (event) => {
      // Ignore if user is typing in an input/textarea
      if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
        return;
      }

      // If menu is open, only handle Left arrow to open it
      // The menu component handles its own navigation (Up/Down/Enter/Left/Esc)
      if (menuOpen) {
        // Only handle opening the menu, not other keys
        return;
      }

      // Prevent default behavior for our handled keys
      if (['ArrowLeft', 'ArrowRight', ' ', 'Enter'].includes(event.key)) {
        event.preventDefault();
        event.stopPropagation();
      }

      switch (event.key) {
        case 'ArrowLeft':
          if (onLeft) onLeft();
          break;
        case 'ArrowRight':
          if (onRight) onRight();
          break;
        case ' ':
          if (onSpace) onSpace();
          break;
        case 'Enter':
          if (onEnter) onEnter();
          break;
        default:
          break;
      }
    };

    // Use capture phase to intercept before it reaches the iframe
    window.addEventListener('keydown', handleKeyDown, true);

    return () => {
      window.removeEventListener('keydown', handleKeyDown, true);
    };
  }, [onLeft, onRight, onSpace, onEnter, menuOpen]);
}

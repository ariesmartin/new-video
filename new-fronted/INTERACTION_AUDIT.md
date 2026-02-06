# Frontend Interaction Audit Report

**Date:** 2026-02-03
**Scope:** `new-fronted/src`
**Focus:** Interactions, State Management, A11y, Touch Support

## Executive Summary
The audit revealed solid architectural foundations (Zustand stores, component separation) but identified critical gaps in **mobile touch support**, **accessibility (A11y)**, and **state hydration**. The Canvas component specifically lacks native touch handling, making it unusable on tablets/phones.

---

## 1. Critical Issues (Logic & State)

### 1.1 `useIsMobile` Hydration Mismatch
- **File:** `src/hooks/use-mobile.ts`
- **Issue:** The hook initializes with `undefined`, then flips to `true/false` after mount. This causes layout shifts and potential hydration errors if server-side rendering is ever introduced.
- **Fix:** Initialize with a safe default (e.g., `false`) or use a layout effect to synchronously set state before paint if client-side only.

### 1.2 `useLocalStorage` Stale Closures
- **File:** `src/hooks/useStore.ts` (lines 465-489)
- **Issue:** The `setValue` function includes `storedValue` in its dependency array. This forces consumers of this hook to re-subscribe/re-render unnecessarily on every value change.
- **Fix:** Use the functional update pattern `setStoredValue(prev => ...)` inside `setValue` to remove the dependency on `storedValue`.

### 1.3 Dead Code / Logic Gaps
- **File:** `src/hooks/useStore.ts`
- **Issue:** `setClipboard` accepts arguments but does nothing, while `setClipboardNodes` exists separately.
- **Risk:** Confusion in API usage leading to features not working.

---

## 2. Major Issues (Interactions & A11y)

### 2.1 Canvas Missing Touch Support
- **File:** `src/components/canvas/StoryboardCanvas.tsx`
- **Issue:** The canvas relies exclusively on `onMouseDown`, `onMouseMove`, `onMouseUp`.
- **Impact:** Panning and Node dragging **will not work** on touch devices (iPad, Mobile).
- **Fix:** Add `onTouchStart`, `onTouchMove`, `onTouchEnd` handlers that map to the existing logic.

### 2.2 Performance Bottleneck in Canvas
- **File:** `src/components/canvas/StoryboardCanvas.tsx`
- **Issue:** `handleMouseMove` updates React state (`setMousePosition`) on every pixel of movement.
- **Impact:** High CPU usage and frame drops on low-end devices.
- **Fix:** Throttle this event handler (e.g., use `requestAnimationFrame` or `lodash.throttle`).

### 2.3 Accessibility (A11y) Violations
- **Global:** Many icon-only buttons (e.g., in `ScriptWorkshopModal.tsx`, `StoryboardCanvas.tsx`) lack `aria-label`.
- **Modals:** `ScriptWorkshopModal.tsx` lacks `role="dialog"`, `aria-modal="true"`, and a Focus Trap. Keyboard users can tab "out" of the modal into the background.
- **Canvas:** The main canvas area is not focusable via keyboard (missing `tabIndex="0"`), making keyboard shortcuts (`Delete`, `Escape`) unreliable unless the user has explicitly clicked the div first.

---

## 3. Recommended Fixes

### Fix 1: Robust `useIsMobile`
```typescript
export function useIsMobile() {
  const [isMobile, setIsMobile] = React.useState(false) // Default to false

  React.useLayoutEffect(() => {
    const mql = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT - 1}px)`)
    const onChange = (e: MediaQueryListEvent) => setIsMobile(e.matches)
    
    setIsMobile(mql.matches) // Set initial value
    mql.addEventListener("change", onChange)
    return () => mql.removeEventListener("change", onChange)
  }, [])

  return isMobile
}
```

### Fix 2: Canvas Touch Handlers
Add these to `StoryboardCanvas.tsx` div:
```tsx
onTouchStart={(e) => {
  if (e.touches.length === 1) {
    // Treat as pan start
    const touch = e.touches[0];
    setIsPanning(true);
    setPanStart({ x: touch.clientX - offset.x, y: touch.clientY - offset.y });
  }
}}
onTouchMove={(e) => {
  if (isPanning && e.touches.length === 1) {
    const touch = e.touches[0];
    setOffset({
      x: touch.clientX - panStart.x,
      y: touch.clientY - panStart.y
    });
  }
}}
onTouchEnd={() => setIsPanning(false)}
```

### Fix 3: Throttled Mouse Move
```typescript
import { throttle } from 'lodash'; // or similar

const handleMouseMove = useCallback(
  throttle((e: React.MouseEvent) => {
    // ... existing logic
  }, 16), // ~60fps
  [isPanning, panStart, offset, zoom]
);
```

### Fix 4: Accessibility
- Add `aria-label="Description"` to all icon buttons.
- Add `role="dialog"` to modal containers.
- Implement a `useEffect` in modals to trap focus or use a library like `@radix-ui/react-dialog` which handles this automatically.

---

## 4. Next Steps
1. Refactor `useIsMobile` and `useLocalStorage`.
2. Implement Touch handlers in `StoryboardCanvas`.
3. Perform an A11y sweep on all Modals.

import React, { useState, useEffect, useLayoutEffect, useRef } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { X } from 'lucide-react'

const STEPS = [
  {
    target: 'nav-home',
    route: '/',
    title: 'Welcome!',
    text: 'This is Home — everything you need is on this one page: upload a file, run a check, and see your results.',
  },
  {
    target: 'upload-card',
    route: '/',
    title: 'Step 1 — Upload',
    text: 'Click here to upload a CSV, Excel, or Parquet file from your computer.',
  },
  {
    target: 'choose-run-card',
    route: '/',
    title: 'Step 2 — Run a Check',
    text: 'Pick the file you uploaded from this list, then click "Run Check" to analyze it.',
  },
  {
    target: 'results-card',
    route: '/',
    title: 'Step 3 — Results',
    text: 'Your quality score and a plain-English breakdown show up here. Click "Show detailed technical breakdown" if you want the full numbers (drift scores, schema changes, per-column stats).',
  },
  {
    target: 'nav-alerts',
    route: '/',
    title: 'Alerts',
    text: 'Anything urgent found during a check shows up here, across all your files.',
  },
  {
    target: 'nav-reports',
    route: '/',
    title: 'Reports',
    text: 'Download a full written report of your results — handy for sharing with someone else.',
  },
  {
    target: 'nav-settings',
    route: '/',
    title: 'Settings',
    text: 'Adjust how strict the checks are and set up email alerts here.',
  },
  {
    target: 'theme-toggle',
    route: '/',
    title: 'Light / Dark Mode',
    text: 'Switch between light and dark mode anytime with this button.',
  },
]

export default function Tour({ onFinish }) {
  const [step, setStep] = useState(0)
  const [rect, setRect] = useState(null)
  const navigate = useNavigate()
  const location = useLocation()
  const current = STEPS[step]

  useEffect(() => {
    if (current.route && location.pathname !== current.route) {
      navigate(current.route)
    }
  }, [step])

  useLayoutEffect(() => {
    let raf
    const measure = () => {
      const el = document.querySelector(`[data-tour="${current.target}"]`)
      if (el) {
        el.scrollIntoView({ block: 'center', behavior: 'instant' })
        setRect(el.getBoundingClientRect())
      } else {
        setRect(null)
      }
    }
    // wait a tick for route change / render to settle
    raf = requestAnimationFrame(() => requestAnimationFrame(measure))
    window.addEventListener('resize', measure)
    return () => {
      cancelAnimationFrame(raf)
      window.removeEventListener('resize', measure)
    }
  }, [step, location.pathname])

  const isLast = step === STEPS.length - 1

  const handleNext = () => {
    if (isLast) onFinish()
    else setStep(step + 1)
  }

  const handleBack = () => {
    if (step > 0) setStep(step - 1)
  }

  const padding = 8
  const box = rect
    ? {
        top: rect.top - padding,
        left: rect.left - padding,
        width: rect.width + padding * 2,
        height: rect.height + padding * 2,
      }
    : null

  // Position tooltip below the highlighted box, or above if it would overflow
  const tooltipWidth = 320
  const viewportH = window.innerHeight
  const viewportW = window.innerWidth
  let tooltipTop = box ? box.top + box.height + 16 : viewportH / 2 - 80
  let tooltipLeft = box ? Math.min(Math.max(box.left, 16), viewportW - tooltipWidth - 16) : viewportW / 2 - tooltipWidth / 2
  if (box && tooltipTop + 180 > viewportH) {
    tooltipTop = Math.max(box.top - 180 - 16, 16)
  }

  return (
    <div className="fixed inset-0 z-[9999]" style={{ pointerEvents: 'none' }}>
      {/* Dark overlay with a cutout for the highlighted element */}
      <svg className="absolute inset-0 w-full h-full" style={{ pointerEvents: 'auto' }}>
        <defs>
          <mask id="tour-mask">
            <rect width="100%" height="100%" fill="white" />
            {box && (
              <rect
                x={box.left}
                y={box.top}
                width={box.width}
                height={box.height}
                rx="12"
                fill="black"
              />
            )}
          </mask>
        </defs>
        <rect width="100%" height="100%" fill="rgba(0,0,0,0.6)" mask="url(#tour-mask)" />
      </svg>

      {box && (
        <div
          className="absolute rounded-xl border-2 border-primary"
          style={{
            top: box.top,
            left: box.left,
            width: box.width,
            height: box.height,
            boxShadow: '0 0 0 4px rgba(102,126,234,0.3)',
          }}
        />
      )}

      {/* Tooltip */}
      <div
        className="absolute bg-white dark:bg-gray-900 rounded-xl shadow-2xl p-5 border border-gray-200 dark:border-gray-800"
        style={{ top: tooltipTop, left: tooltipLeft, width: tooltipWidth, pointerEvents: 'auto' }}
      >
        <div className="flex items-start justify-between mb-2">
          <p className="font-bold text-gray-900 dark:text-white">{current.title}</p>
          <button onClick={onFinish} className="text-gray-400 hover:text-gray-600">
            <X size={18} />
          </button>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">{current.text}</p>
        <div className="flex items-center justify-between">
          <p className="text-xs text-gray-400">{step + 1} of {STEPS.length}</p>
          <div className="flex gap-2">
            {step > 0 && (
              <button
                onClick={handleBack}
                className="px-3 py-1.5 text-sm rounded-lg bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700"
              >
                Back
              </button>
            )}
            <button
              onClick={handleNext}
              className="px-3 py-1.5 text-sm rounded-lg bg-gradient-primary text-white font-medium"
            >
              {isLast ? 'Done' : 'Next'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

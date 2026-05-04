'use client';

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';

/* ─── Data ──────────────────────────────────────────────────────────────── */

const plans = [
  {
    name: 'Free',
    monthlyPrice: 0,
    annualPrice: 0,
    description: 'Perfect for exploring AI video creation.',
    badge: null,
    buttonText: 'Get Started Free',
    href: '/register',
    features: [
      { text: '3 videos per month', included: true },
      { text: 'SD resolution (480p)', included: true },
      { text: 'AI story generation', included: true },
      { text: 'Scene breakdown', included: true },
      { text: 'Basic image generation', included: true },
      { text: '5 min max video length', included: true },
      { text: 'No watermark', included: false },
      { text: 'Voice narration', included: false },
      { text: 'Background music', included: false },
      { text: 'API access', included: false },
    ],
  },
  {
    name: 'Pro',
    monthlyPrice: 29,
    annualPrice: 19,
    description: 'For creators who want professional results.',
    badge: 'Most Popular',
    buttonText: 'Start Pro Plan',
    href: '/register?plan=pro',
    features: [
      { text: '30 videos per month', included: true },
      { text: 'HD resolution (1080p)', included: true },
      { text: 'Advanced AI story generation', included: true },
      { text: 'Scene breakdown & editing', included: true },
      { text: 'Premium image generation', included: true },
      { text: '30 min max video length', included: true },
      { text: 'No watermark', included: true },
      { text: 'AI voice narration', included: true },
      { text: 'AI background music', included: true },
      { text: 'Priority support', included: true },
    ],
  },
  {
    name: 'Enterprise',
    monthlyPrice: 99,
    annualPrice: 69,
    description: 'For studios and teams operating at scale.',
    badge: 'Best Value',
    buttonText: 'Contact Sales',
    href: '/contact',
    features: [
      { text: 'Unlimited videos', included: true },
      { text: '4K resolution', included: true },
      { text: 'Everything in Pro', included: true },
      { text: 'API access', included: true },
      { text: 'Team collaboration (5 seats)', included: true },
      { text: 'Priority rendering queue', included: true },
      { text: 'Custom AI fine-tuning', included: true },
      { text: 'Advanced analytics', included: true },
      { text: 'Dedicated support manager', included: true },
      { text: 'SLA guarantee', included: true },
    ],
  },
];

const faqs = [
  {
    q: 'Can I change my plan anytime?',
    a: "Yes, you can upgrade or downgrade at any time. Changes take effect immediately and you'll be charged or credited the prorated difference.",
  },
  {
    q: 'What happens when I reach my video limit?',
    a: "When you hit your monthly limit you'll be prompted to upgrade. All existing videos remain fully accessible—nothing is deleted.",
  },
  {
    q: 'Do you offer refunds?',
    a: 'We offer a 14-day money-back guarantee on all paid plans. Contact us within 14 days of purchase for a full refund—no questions asked.',
  },
  {
    q: 'What AI models power CineCraft?',
    a: 'CineCraft integrates best-in-class models for every step: advanced LLMs for story generation, Stable Diffusion / DALL-E for images, ElevenLabs for voice, and generative music models for soundtracks. We continuously upgrade as better models are released.',
  },
  {
    q: 'Can I cancel anytime?',
    a: 'Absolutely—no long-term contracts. Cancel any time from your account settings. Your access continues until the end of the current billing period.',
  },
];

/* ─── Sub-components ─────────────────────────────────────────────────────── */

function CheckIcon() {
  return (
    <span className="flex-shrink-0 w-5 h-5 rounded-full bg-indigo-600/25 flex items-center justify-center mt-0.5">
      <svg className="w-3 h-3 text-indigo-400" viewBox="0 0 12 12" fill="none">
        <path
          d="M2 6l3 3 5-5"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </span>
  );
}

function CrossIcon() {
  return (
    <span className="flex-shrink-0 w-5 h-5 rounded-full bg-gray-800 flex items-center justify-center mt-0.5">
      <svg className="w-3 h-3 text-gray-600" viewBox="0 0 12 12" fill="none">
        <path
          d="M3 3l6 6M9 3l-6 6"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
        />
      </svg>
    </span>
  );
}

/* Ripple button wrapper */
function RippleLink({
  href,
  children,
  className,
}: {
  href: string;
  children: React.ReactNode;
  className: string;
}) {
  const ref = useRef<HTMLAnchorElement>(null);

  function handleClick(e: React.MouseEvent<HTMLAnchorElement>) {
    const el = ref.current;
    if (!el) return;

    const rect = el.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const ripple = document.createElement('span');
    ripple.style.cssText = `
      position:absolute;
      border-radius:50%;
      background:rgba(255,255,255,0.25);
      transform:scale(0);
      animation:ripple 0.6s linear;
      width:150px;height:150px;
      left:${x - 75}px;top:${y - 75}px;
      pointer-events:none;
    `;
    el.style.position = 'relative';
    el.style.overflow = 'hidden';
    el.appendChild(ripple);
    setTimeout(() => ripple.remove(), 700);
  }

  return (
    <a ref={ref} href={href} onClick={handleClick} className={className}>
      {children}
    </a>
  );
}

/* Accordion item */
function AccordionItem({
  faq,
  open,
  onToggle,
}: {
  faq: { q: string; a: string };
  open: boolean;
  onToggle: () => void;
}) {
  const bodyRef = useRef<HTMLDivElement>(null);
  const [height, setHeight] = useState(0);

  useEffect(() => {
    if (bodyRef.current) setHeight(bodyRef.current.scrollHeight);
  }, []);

  return (
    <div className="border border-gray-700/60 rounded-xl overflow-hidden bg-white/[0.03] hover:border-gray-600 transition-colors">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between px-6 py-5 text-left text-white font-medium hover:bg-white/5 transition-colors"
      >
        <span>{faq.q}</span>
        <span
          className="ml-4 flex-shrink-0 transition-transform duration-300"
          style={{ transform: open ? 'rotate(45deg)' : 'rotate(0deg)' }}
        >
          <svg className="w-5 h-5 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
            <path d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" />
          </svg>
        </span>
      </button>

      <div
        style={{
          maxHeight: open ? `${height}px` : '0px',
          opacity: open ? 1 : 0,
          transition: 'max-height 0.35s ease, opacity 0.25s ease',
          overflow: 'hidden',
        }}
      >
        <div ref={bodyRef} className="px-6 pb-5 text-gray-400 text-sm leading-relaxed">
          {faq.a}
        </div>
      </div>
    </div>
  );
}

/* ─── Page ───────────────────────────────────────────────────────────────── */

export default function PricingPage() {
  const [isAnnual, setIsAnnual] = useState(false);
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  return (
    <>
      {/* Ripple keyframe injected once */}
      <style>{`
        @keyframes ripple {
          to { transform: scale(4); opacity: 0; }
        }
      `}</style>

      <div className="min-h-screen bg-[#080c14]">
        {/* Ambient glow blobs */}
        <div
          aria-hidden
          className="pointer-events-none fixed inset-0 overflow-hidden"
        >
          <div className="absolute -top-40 -left-40 w-[600px] h-[600px] rounded-full bg-indigo-700/20 blur-[120px]" />
          <div className="absolute top-1/3 right-0 w-[500px] h-[500px] rounded-full bg-purple-700/15 blur-[120px]" />
          <div className="absolute bottom-0 left-1/2 w-[400px] h-[400px] rounded-full bg-indigo-800/20 blur-[100px]" />
        </div>

        {/* ── Nav ── */}
        <header className="relative z-10 border-b border-white/[0.07] bg-black/20 backdrop-blur-md">
          <nav className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="flex h-16 items-center justify-between">
              <Link href="/" className="flex items-center gap-2 group">
                <div className="h-8 w-8 rounded-lg bg-indigo-600 flex items-center justify-center group-hover:bg-indigo-500 transition-colors">
                  <span className="text-white font-bold text-xl">C</span>
                </div>
                <span className="text-xl font-bold text-white">CineCraft</span>
              </Link>
              <div className="flex items-center gap-6">
                <Link
                  href="/"
                  className="text-gray-400 hover:text-white transition-colors text-sm font-medium"
                >
                  Home
                </Link>
                <Link
                  href="/login"
                  className="text-gray-400 hover:text-white transition-colors text-sm font-medium"
                >
                  Login
                </Link>
                <Link
                  href="/register"
                  className="bg-indigo-600 hover:bg-indigo-500 active:scale-95 text-white px-4 py-2 rounded-lg text-sm font-semibold transition-all hover:scale-105"
                >
                  Get Started
                </Link>
              </div>
            </div>
          </nav>
        </header>

        <main className="relative z-10 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-20">
          {/* ── Hero text ── */}
          <div className="text-center mb-16">
            {/* Offer pill */}
            <div className="inline-flex items-center gap-2 bg-indigo-600/15 border border-indigo-500/30 rounded-full px-4 py-1.5 mb-8 text-sm text-indigo-300 font-medium">
              <span className="w-2 h-2 bg-indigo-400 rounded-full animate-pulse" />
              Limited Time Offer! Save 34% with Annual Billing
            </div>

            <h1 className="text-5xl sm:text-6xl font-bold text-white tracking-tight mb-5 leading-tight">
              Simple, transparent{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400">
                pricing
              </span>
            </h1>
            <p className="text-gray-400 text-lg max-w-xl mx-auto leading-relaxed">
              Choose the plan that fits your creative vision. Upgrade or downgrade
              at any time—no hidden fees.
            </p>

            {/* Billing toggle */}
            <div className="flex items-center justify-center gap-4 mt-10">
              <span
                className={`text-sm font-semibold transition-colors ${
                  !isAnnual ? 'text-white' : 'text-gray-500'
                }`}
              >
                Monthly
              </span>

              <button
                onClick={() => setIsAnnual((v) => !v)}
                aria-label="Toggle billing period"
                className={`relative inline-flex h-7 w-14 flex-shrink-0 items-center rounded-full transition-colors duration-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 ${
                  isAnnual ? 'bg-indigo-600' : 'bg-gray-700'
                }`}
              >
                <span
                  className={`inline-block h-5 w-5 rounded-full bg-white shadow-md transform transition-transform duration-300 ${
                    isAnnual ? 'translate-x-8' : 'translate-x-1'
                  }`}
                />
              </button>

              <span
                className={`text-sm font-semibold transition-colors ${
                  isAnnual ? 'text-white' : 'text-gray-500'
                }`}
              >
                Annual
              </span>

              <span className="bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 text-xs font-bold px-2.5 py-1 rounded-full tracking-wide">
                SAVE 34%
              </span>
            </div>
          </div>

          {/* ── Plan cards ── */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8 mb-28">
            {plans.map((plan) => {
              const isPopular = plan.badge === 'Most Popular';
              const isBest = plan.badge === 'Best Value';
              const price = isAnnual ? plan.annualPrice : plan.monthlyPrice;

              return (
                <div
                  key={plan.name}
                  className={[
                    'relative rounded-2xl border p-8 flex flex-col',
                    'transition-all duration-300 ease-out',
                    isPopular
                      ? [
                          'border-indigo-500 bg-indigo-600/10',
                          'shadow-[0_0_50px_rgba(99,102,241,0.18)]',
                          'hover:shadow-[0_0_80px_rgba(99,102,241,0.35)]',
                          'scale-[1.03] hover:scale-[1.065]',
                        ].join(' ')
                      : [
                          'border-gray-700/50 bg-white/[0.03]',
                          'hover:border-indigo-500/50 hover:bg-indigo-600/[0.06]',
                          'hover:scale-[1.025] hover:shadow-2xl',
                        ].join(' '),
                  ].join(' ')}
                >
                  {/* Badge */}
                  {plan.badge && (
                    <div
                      className={[
                        'absolute -top-4 left-1/2 -translate-x-1/2',
                        'px-4 py-1 rounded-full text-xs font-bold uppercase tracking-widest',
                        isPopular
                          ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/40'
                          : 'bg-emerald-600 text-white shadow-lg shadow-emerald-500/30',
                      ].join(' ')}
                    >
                      {plan.badge}
                    </div>
                  )}

                  {/* Plan name + desc */}
                  <div className="mb-1">
                    <h3 className="text-xl font-bold text-white">{plan.name}</h3>
                    <p className="text-gray-400 text-sm mt-1.5 leading-snug">
                      {plan.description}
                    </p>
                  </div>

                  {/* Price */}
                  <div className="my-6">
                    <div className="flex items-end gap-1">
                      <span className="text-gray-400 text-lg self-start mt-2">$</span>
                      <span className="text-[3.25rem] font-extrabold text-white leading-none tabular-nums">
                        {price}
                      </span>
                      <span className="text-gray-400 text-sm mb-1.5">/month</span>
                    </div>
                    <p className="text-gray-600 text-xs mt-2 h-4">
                      {isAnnual && plan.monthlyPrice > 0 ? (
                        <>
                          <span className="line-through mr-1">${plan.monthlyPrice}/month</span>
                          · billed annually
                        </>
                      ) : plan.monthlyPrice > 0 ? (
                        'billed monthly'
                      ) : (
                        'free forever'
                      )}
                    </p>
                  </div>

                  {/* CTA */}
                  <RippleLink
                    href={plan.href}
                    className={[
                      'w-full py-3 px-6 rounded-xl font-semibold text-sm text-center',
                      'transition-all duration-200 active:scale-95 mb-8 select-none',
                      isPopular
                        ? 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-500/30 hover:shadow-indigo-500/50'
                        : isBest
                        ? 'bg-emerald-600/20 hover:bg-emerald-600/30 border border-emerald-500/40 text-emerald-300 hover:text-emerald-200'
                        : 'border border-gray-600 text-gray-200 hover:border-indigo-500 hover:text-white hover:bg-indigo-600/10',
                    ].join(' ')}
                  >
                    {plan.buttonText}
                  </RippleLink>

                  {/* Divider */}
                  <div className="border-t border-gray-700/50 mb-6" />

                  {/* Features */}
                  <ul className="space-y-3 flex-1">
                    {plan.features.map((f) => (
                      <li key={f.text} className="flex items-start gap-3">
                        {f.included ? <CheckIcon /> : <CrossIcon />}
                        <span
                          className={`text-sm leading-snug ${
                            f.included ? 'text-gray-200' : 'text-gray-600 line-through'
                          }`}
                        >
                          {f.text}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
          </div>

          {/* ── FAQ ── */}
          <div className="max-w-3xl mx-auto mb-24">
            <h2 className="text-3xl font-bold text-white text-center mb-3">
              Frequently asked questions
            </h2>
            <p className="text-gray-500 text-center mb-12 text-sm">
              Can't find the answer you're looking for? Reach out to our support team.
            </p>

            <div className="space-y-3">
              {faqs.map((faq, i) => (
                <AccordionItem
                  key={i}
                  faq={faq}
                  open={openFaq === i}
                  onToggle={() => setOpenFaq(openFaq === i ? null : i)}
                />
              ))}
            </div>
          </div>

          {/* ── Bottom CTA ── */}
          <div className="text-center">
            <div className="inline-block bg-gradient-to-br from-indigo-600/10 to-purple-600/10 border border-indigo-500/25 rounded-2xl px-12 py-10 max-w-xl w-full">
              <div className="w-12 h-12 rounded-2xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center mx-auto mb-5">
                <svg
                  className="w-6 h-6 text-indigo-400"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                </svg>
              </div>
              <h3 className="text-2xl font-bold text-white mb-2">
                Still have questions?
              </h3>
              <p className="text-gray-400 text-sm mb-7 leading-relaxed">
                Our team is ready to help you find the perfect plan for your creative needs.
              </p>
              <RippleLink
                href="mailto:support@cinecraft.ai"
                className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 active:scale-95 text-white px-6 py-3 rounded-xl font-semibold text-sm transition-all hover:scale-105"
              >
                Contact Support
                <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z" />
                  <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z" />
                </svg>
              </RippleLink>
            </div>
          </div>
        </main>
      </div>
    </>
  );
}

'use client';

import { useState, useRef } from 'react';
import Link from 'next/link';

const plans = [
  {
    name: 'Free',
    monthlyPrice: 0,
    annualPrice: 0,
    description: 'Explore AI video creation at no cost.',
    badge: null,
    buttonText: 'Get Started Free',
    href: '/register',
    features: [
      { text: '3 videos / month', included: true },
      { text: 'SD resolution (480p)', included: true },
      { text: 'AI story generation', included: true },
      { text: 'Scene breakdown', included: true },
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
    description: 'For creators who demand professional results.',
    badge: 'Most Popular',
    buttonText: 'Start Pro Plan',
    href: '/register?plan=pro',
    features: [
      { text: '30 videos / month', included: true },
      { text: 'HD resolution (1080p)', included: true },
      { text: 'Advanced AI story generation', included: true },
      { text: 'Scene breakdown & editing', included: true },
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
    description: 'Unlimited scale for studios and teams.',
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
      { text: 'Dedicated support', included: true },
    ],
  },
];

function CheckIcon() {
  return (
    <span className="flex-shrink-0 w-5 h-5 rounded-full bg-indigo-100 flex items-center justify-center mt-0.5">
      <svg className="w-3 h-3 text-indigo-600" viewBox="0 0 12 12" fill="none">
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
    <span className="flex-shrink-0 w-5 h-5 rounded-full bg-gray-100 flex items-center justify-center mt-0.5">
      <svg className="w-3 h-3 text-gray-400" viewBox="0 0 12 12" fill="none">
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
      position:absolute;border-radius:50%;
      background:rgba(255,255,255,0.35);
      transform:scale(0);animation:cc-ripple 0.55s linear;
      width:150px;height:150px;
      left:${x - 75}px;top:${y - 75}px;
      pointer-events:none;
    `;
    el.style.position = 'relative';
    el.style.overflow = 'hidden';
    el.appendChild(ripple);
    setTimeout(() => ripple.remove(), 650);
  }

  return (
    <a ref={ref} href={href} onClick={handleClick} className={className}>
      {children}
    </a>
  );
}

export default function PricingSection() {
  const [isAnnual, setIsAnnual] = useState(false);

  return (
    <section className="bg-gray-50 border-t border-gray-100">
      <style>{`@keyframes cc-ripple{to{transform:scale(4);opacity:0;}}`}</style>

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-24">
        {/* Heading */}
        <div className="text-center mb-14">
          <p className="text-sm font-semibold text-indigo-600 uppercase tracking-widest mb-3">
            Pricing
          </p>
          <h2 className="text-4xl sm:text-5xl font-bold text-gray-900 tracking-tight">
            Choose your plan
          </h2>
          <p className="mt-4 text-gray-500 text-lg max-w-xl mx-auto">
            Start free, upgrade when you're ready. No hidden fees.
          </p>

          {/* Toggle */}
          <div className="flex items-center justify-center gap-4 mt-8">
            <span
              className={`text-sm font-semibold transition-colors ${
                !isAnnual ? 'text-gray-900' : 'text-gray-400'
              }`}
            >
              Monthly
            </span>

            <button
              onClick={() => setIsAnnual((v) => !v)}
              aria-label="Toggle billing period"
              className={`relative inline-flex h-7 w-14 flex-shrink-0 items-center rounded-full transition-colors duration-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 ${
                isAnnual ? 'bg-indigo-600' : 'bg-gray-300'
              }`}
            >
              <span
                className={`inline-block h-5 w-5 rounded-full bg-white shadow-sm transform transition-transform duration-300 ${
                  isAnnual ? 'translate-x-8' : 'translate-x-1'
                }`}
              />
            </button>

            <span
              className={`text-sm font-semibold transition-colors ${
                isAnnual ? 'text-gray-900' : 'text-gray-400'
              }`}
            >
              Annual
            </span>

            <span className="bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-bold px-2.5 py-1 rounded-full tracking-wide">
              SAVE 34%
            </span>
          </div>
        </div>

        {/* Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8">
          {plans.map((plan) => {
            const isPopular = plan.badge === 'Most Popular';
            const isBest = plan.badge === 'Best Value';
            const price = isAnnual ? plan.annualPrice : plan.monthlyPrice;

            return (
              <div
                key={plan.name}
                className={[
                  'relative rounded-2xl border p-8 flex flex-col bg-white',
                  'transition-all duration-300 ease-out',
                  isPopular
                    ? [
                        'border-indigo-500 ring-1 ring-indigo-500',
                        'shadow-[0_8px_40px_rgba(99,102,241,0.18)]',
                        'hover:shadow-[0_12px_60px_rgba(99,102,241,0.30)]',
                        'scale-[1.03] hover:scale-[1.055]',
                      ].join(' ')
                    : [
                        'border-gray-200 shadow-sm',
                        'hover:border-indigo-300 hover:shadow-lg hover:scale-[1.025]',
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
                        ? 'bg-indigo-600 text-white shadow-md shadow-indigo-300'
                        : 'bg-emerald-500 text-white shadow-md shadow-emerald-200',
                    ].join(' ')}
                  >
                    {plan.badge}
                  </div>
                )}

                {/* Name + desc */}
                <div className="mb-1">
                  <h3 className="text-xl font-bold text-gray-900">{plan.name}</h3>
                  <p className="text-gray-500 text-sm mt-1.5 leading-snug">
                    {plan.description}
                  </p>
                </div>

                {/* Price */}
                <div className="my-6">
                  <div className="flex items-end gap-1">
                    <span className="text-gray-400 text-lg self-start mt-2">$</span>
                    <span className="text-[3.25rem] font-extrabold text-gray-900 leading-none tabular-nums">
                      {price}
                    </span>
                    <span className="text-gray-400 text-sm mb-1.5">/month</span>
                  </div>
                  <p className="text-gray-400 text-xs mt-2 h-4">
                    {isAnnual && plan.monthlyPrice > 0 ? (
                      <>
                        <span className="line-through mr-1">${plan.monthlyPrice}/mo</span>
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
                      ? 'bg-indigo-600 hover:bg-indigo-700 text-white shadow-md shadow-indigo-200 hover:shadow-indigo-300'
                      : isBest
                      ? 'bg-emerald-50 hover:bg-emerald-100 border border-emerald-300 text-emerald-700'
                      : 'border border-gray-300 text-gray-700 hover:border-indigo-400 hover:text-indigo-700 hover:bg-indigo-50',
                  ].join(' ')}
                >
                  {plan.buttonText}
                </RippleLink>

                {/* Divider */}
                <div className="border-t border-gray-100 mb-6" />

                {/* Features */}
                <ul className="space-y-3 flex-1">
                  {plan.features.map((f) => (
                    <li key={f.text} className="flex items-start gap-3">
                      {f.included ? <CheckIcon /> : <CrossIcon />}
                      <span
                        className={`text-sm leading-snug ${
                          f.included ? 'text-gray-700' : 'text-gray-400 line-through'
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

        {/* Link to full pricing page */}
        <div className="text-center mt-12">
          <Link
            href="/pricing"
            className="inline-flex items-center gap-1.5 text-indigo-600 hover:text-indigo-800 font-medium text-sm transition-colors group"
          >
            View full pricing details
            <svg
              className="w-4 h-4 transition-transform group-hover:translate-x-0.5"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                clipRule="evenodd"
              />
            </svg>
          </Link>
        </div>
      </div>
    </section>
  );
}

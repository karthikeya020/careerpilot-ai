"use client";

/** A tiny laptop booting up -- shown while the live job feed loads. */
export function LaptopBoot() {
  return (
    <div className="flex flex-col items-center gap-3 py-12">
      <style>{`
        .lb-wrap{width:104px}
        .lb-screen{
          position:relative;height:64px;border:2px solid var(--color-border-strong);
          border-radius:8px 8px 2px 2px;background:#0b0b16;overflow:hidden;
          animation:lb-power 2s ease-in-out infinite;
        }
        .lb-base{
          height:7px;width:124px;margin:-1px 0 0 -12px;border-radius:0 0 7px 7px;
          background:linear-gradient(180deg,var(--color-border-strong),var(--color-surface-muted));
        }
        .lb-scan{position:absolute;left:0;right:0;height:14px;
          background:linear-gradient(180deg,transparent,color-mix(in srgb,var(--color-brand) 55%,transparent),transparent);
          animation:lb-scan 2s linear infinite;}
        .lb-logo{position:absolute;top:14px;left:50%;width:14px;height:14px;margin-left:-7px;border-radius:50%;
          background:var(--color-brand);box-shadow:0 0 14px var(--color-brand);opacity:0;
          animation:lb-logo 2s ease-in-out infinite;}
        .lb-bar{position:absolute;left:16px;right:16px;bottom:12px;height:5px;border-radius:3px;
          background:color-mix(in srgb,var(--color-brand) 18%,transparent);overflow:hidden;}
        .lb-bar i{display:block;height:100%;width:0;border-radius:3px;background:var(--color-brand);
          animation:lb-fill 2s cubic-bezier(.3,.1,.3,1) infinite;}
        .lb-dots::after{content:"";animation:lb-dots 1.4s steps(4,end) infinite;}
        @keyframes lb-power{0%,12%{background:#0b0b16}30%,100%{background:#10101f}}
        @keyframes lb-scan{0%{transform:translateY(-16px)}45%{transform:translateY(64px)}100%{transform:translateY(64px)}}
        @keyframes lb-logo{0%,18%{opacity:0;transform:scale(.6)}40%{opacity:1;transform:scale(1)}
          70%{opacity:.85;transform:scale(1.05)}100%{opacity:1;transform:scale(1)}}
        @keyframes lb-fill{0%,30%{width:0}80%{width:100%}100%{width:100%}}
        @keyframes lb-dots{0%{content:""}25%{content:"."}50%{content:".."}75%{content:"..."}100%{content:""}}
        @media (prefers-reduced-motion:reduce){
          .lb-screen{animation:none;background:#10101f}
          .lb-scan,.lb-bar i,.lb-dots::after{animation:none}
          .lb-logo{animation:none;opacity:1}
          .lb-bar i{width:70%}
        }
      `}</style>
      <div className="lb-wrap">
        <div className="lb-screen">
          <span className="lb-scan" />
          <span className="lb-logo" />
          <span className="lb-bar">
            <i />
          </span>
        </div>
        <div className="lb-base" />
      </div>
      <p className="text-xs text-muted">
        searching jobs for you<span className="lb-dots" />
      </p>
    </div>
  );
}

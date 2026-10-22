export const $ = (id) => document.getElementById(id);

export const el = (tag, attrs = {}, ...children) => {
  const node = document.createElement(tag);
  Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, value));
  node.append(...children);
  return node;
};

export const reducedMotion = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;

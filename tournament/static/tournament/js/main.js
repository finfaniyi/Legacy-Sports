console.log("HOME HERO JS LOADED");

document.addEventListener("DOMContentLoaded", () => {
  const slides = document.querySelectorAll(".home-hero-slide");
  const dots = document.querySelectorAll(".home-dot");
  const hero = document.querySelector(".home-hero");

  console.log("Slides:", slides.length, "Dots:", dots.length);

  if (!slides.length || !dots.length || !hero) return;

  let currentSlide = 0;
  let intervalId = null;
  const INTERVAL_TIME = 4500;

  function showSlide(index) {
    slides.forEach(s => s.classList.remove("active"));
    dots.forEach(d => d.classList.remove("active"));

    slides[index].classList.add("active");
    dots[index].classList.add("active");
    currentSlide = index;
  }

  function nextSlide() {
    const next = (currentSlide + 1) % slides.length;
    showSlide(next);
  }

  function startCarousel() {
    stopCarousel(); // prevent stacking
    intervalId = setInterval(nextSlide, INTERVAL_TIME);
  }

  function stopCarousel() {
    if (intervalId) {
      clearInterval(intervalId);
      intervalId = null;
    }
  }

  // Dot navigation
  dots.forEach(dot => {
    dot.addEventListener("click", () => {
      showSlide(Number(dot.dataset.slide));
      startCarousel();
    });
  });

  // Pause on hover
  hero.addEventListener("mouseenter", stopCarousel);
  hero.addEventListener("mouseleave", startCarousel);

  // Start it
  startCarousel();
});


document.addEventListener("DOMContentLoaded", () => {
  const sliceConfigs = {
    ".slice-1": [
      "/static/tournament/images/dodgeball.jpg",
      "/static/tournament/images/dodgeball2.jpg",
      "/static/tournament/images/dodgeball3.jpg",
    ],
    ".slice-2": [
      "/static/tournament/images/back1.jpg",
      "/static/tournament/images/back2.jpg",
    ],
    ".slice-3": [
      "/static/tournament/images/trophy-lift-overlay.webp",
      "/static/tournament/images/rules.jpg",
    ],
    ".slice-4": [
      "/static/tournament/images/volleyball.jpg",
      "/static/tournament/images/back3.jpg",
    ],
  };

  const sliceState = {};

  Object.keys(sliceConfigs).forEach((selector) => {
    const slice = document.querySelector(selector);
    if (!slice) return;

    sliceState[selector] = 0;
    slice.style.backgroundImage = `url(${sliceConfigs[selector][0]})`;
  });

  setInterval(() => {
    Object.keys(sliceConfigs).forEach((selector) => {
      const slice = document.querySelector(selector);
      if (!slice) return;

      const images = sliceConfigs[selector];
      sliceState[selector] =
        (sliceState[selector] + 1) % images.length;

      slice.style.opacity = "0";

      setTimeout(() => {
        slice.style.backgroundImage = `url(${images[sliceState[selector]]})`;
        slice.style.opacity = "1";
      }, 400);
    });
  }, 5000); // 5s interval
});

const slides = document.querySelectorAll(".home-hero-slide");
const dots = document.querySelectorAll(".home-dot");
const prevBtn = document.querySelector(".hero-prev");
const nextBtn = document.querySelector(".hero-next");

let currentSlide = 0;

function showSlide(index) {
  slides.forEach((slide, i) => {
    slide.classList.remove("active");
    dots[i].classList.remove("active");
  });

  slides[index].classList.add("active");
  dots[index].classList.add("active");
  currentSlide = index;
}

nextBtn.addEventListener("click", () => {
  let next = (currentSlide + 1) % slides.length;
  showSlide(next);
});

prevBtn.addEventListener("click", () => {
  let prev = (currentSlide - 1 + slides.length) % slides.length;
  showSlide(prev);
});


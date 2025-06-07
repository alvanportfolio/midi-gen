// Main JavaScript file for MIDI Generator Piano Roll website

document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu toggle
    const menuToggle = document.querySelector('.menu-toggle');
    const nav = document.querySelector('nav');
    
    if (menuToggle) {
        menuToggle.addEventListener('click', function() {
            nav.classList.toggle('active');
            menuToggle.classList.toggle('active');
            
            // Toggle icon
            const icon = menuToggle.querySelector('i');
            if (icon.classList.contains('fa-bars')) {
                icon.classList.remove('fa-bars');
                icon.classList.add('fa-times');
            } else {
                icon.classList.remove('fa-times');
                icon.classList.add('fa-bars');
            }
        });
    }
    
    // Close mobile menu when clicking outside
    document.addEventListener('click', function(event) {
        if (nav && nav.classList.contains('active') && !nav.contains(event.target) && !menuToggle.contains(event.target)) {
            nav.classList.remove('active');
            menuToggle.classList.remove('active');
            
            const icon = menuToggle.querySelector('i');
            icon.classList.remove('fa-times');
            icon.classList.add('fa-bars');
        }
    });
    
    // Header shrink on scroll
    const header = document.querySelector('header');
    let lastScrollTop = 0;
    
    window.addEventListener('scroll', function() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        if (scrollTop > 50) {
            header.classList.add('shrink');
        } else {
            header.classList.remove('shrink');
        }
        
        lastScrollTop = scrollTop;
    });
    
    // Scroll to top button
    const scrollTopBtn = document.createElement('div');
    scrollTopBtn.classList.add('scroll-top');
    scrollTopBtn.innerHTML = '<i class="fas fa-arrow-up"></i>';
    document.body.appendChild(scrollTopBtn);
    
    scrollTopBtn.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
    
    window.addEventListener('scroll', function() {
        if (window.pageYOffset > 300) {
            scrollTopBtn.classList.add('visible');
        } else {
            scrollTopBtn.classList.remove('visible');
        }
    });
    
    // Syntax highlighting for code blocks
    document.querySelectorAll('pre code').forEach(block => {
        // Simple syntax highlighting
        highlightSyntax(block);
    });
    
    // Add smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                const headerOffset = 80; // Adjust based on your header height
                const elementPosition = targetElement.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - headerOffset;
                
                window.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth'
                });
                
                // Close mobile menu if open
                if (nav && nav.classList.contains('active')) {
                    nav.classList.remove('active');
                    menuToggle.classList.remove('active');
                    
                    const icon = menuToggle.querySelector('i');
                    icon.classList.remove('fa-times');
                    icon.classList.add('fa-bars');
                }
            }
        });
    });
    
    // Initialize image lazy loading
    lazyLoadImages();
    
    // Add animation when elements come into view
    animateOnScroll();
});

// Function to highlight syntax in code blocks
function highlightSyntax(codeBlock) {
    if (!codeBlock || !codeBlock.textContent) return;
    
    let html = codeBlock.textContent;
    
    // Python syntax highlighting (simplified)
    const keywords = ['class', 'def', 'return', 'import', 'from', 'self', 'super', 'None', 'True', 'False', '__init__'];
    const functions = ['generate', 'get_parameter_info', 'Note'];
    
    // Replace keywords with spans
    keywords.forEach(keyword => {
        const regex = new RegExp(`\\b${keyword}\\b`, 'g');
        html = html.replace(regex, `<span class="keyword">${keyword}</span>`);
    });
    
    // Replace functions with spans
    functions.forEach(func => {
        const regex = new RegExp(`\\b${func}\\b`, 'g');
        html = html.replace(regex, `<span class="function">${func}</span>`);
    });
    
    // Replace strings
    html = html.replace(/(["'])(.*?)\1/g, '<span class="string">$1$2$1</span>');
    
    // Replace numbers
    html = html.replace(/\b(\d+)\b/g, '<span class="number">$1</span>');
    
    // Replace comments
    html = html.replace(/(#.*)$/gm, '<span class="comment">$1</span>');
    
    codeBlock.innerHTML = html;
}

// Function to lazy load images
function lazyLoadImages() {
    const lazyImages = document.querySelectorAll('img[data-src]');
    
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                    imageObserver.unobserve(img);
                }
            });
        });
        
        lazyImages.forEach(img => {
            imageObserver.observe(img);
        });
    } else {
        // Fallback for browsers without IntersectionObserver
        lazyImages.forEach(img => {
            img.src = img.dataset.src;
            img.removeAttribute('data-src');
        });
    }
}

// Function to animate elements when they come into view
function animateOnScroll() {
    const elements = document.querySelectorAll('.animate-on-scroll');
    
    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animated');
                    observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.1
        });
        
        elements.forEach(el => {
            observer.observe(el);
        });
    } else {
        // Fallback for browsers without IntersectionObserver
        elements.forEach(el => {
            el.classList.add('animated');
        });
    }
}

// Function to create a typed text effect
function createTypedEffect(element, texts, speed = 100, delay = 2000) {
    if (!element) return;
    
    let textIndex = 0;
    let charIndex = 0;
    let isDeleting = false;
    let typingDelay = speed;
    
    function type() {
        const currentText = texts[textIndex];
        
        if (isDeleting) {
            element.textContent = currentText.substring(0, charIndex - 1);
            charIndex--;
            typingDelay = speed / 2; // Delete faster than type
        } else {
            element.textContent = currentText.substring(0, charIndex + 1);
            charIndex++;
            typingDelay = speed;
        }
        
        if (!isDeleting && charIndex === currentText.length) {
            // Finished typing
            isDeleting = true;
            typingDelay = delay; // Wait before deleting
        } else if (isDeleting && charIndex === 0) {
            // Finished deleting
            isDeleting = false;
            textIndex = (textIndex + 1) % texts.length; // Move to next text
        }
        
        setTimeout(type, typingDelay);
    }
    
    type(); // Start the typing effect
}

// Demo initializer for typed effect if element exists
const typedElement = document.querySelector('.typed-text');
if (typedElement) {
    createTypedEffect(
        typedElement,
        ['Generate MIDI with motifs', 'Create melodies with Markov chains', 'Customize your piano roll', 'Export to standard MIDI'],
        100,
        2000
    );
}
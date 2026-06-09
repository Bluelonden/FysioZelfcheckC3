(function (root, factory) {
    if (typeof define === 'function' && define.amd) {
        define([], factory(root));
    } else {
        root.gauge = factory(root);
    }
})(typeof global !== "undefined" ? global : this.window || this.global, function (root) {
    'use strict';

    const gauges = {};

    const createGauge = (selector) => {
        let container;
        let title;
        let indicator;

        const values = {
            min: 0,
            max: 100,
            current: 0
        };

        const update = () => {
            let degrees;

            container.dataset.current = values.current;

            degrees =
                values.current >= values.max
                    ? 180
                    : Math.round((values.current / values.max) * 180);

            title.textContent = values.current;

            indicator.style.setProperty(
                '--gauge-rotation',
                `${degrees}deg`
            );

            indicator.classList.remove(
                'gauge-1',
                'gauge-2',
                'gauge-3',
                'gauge-4',
                'gauge-5'
            );

            if (degrees <= 36) {
                indicator.classList.add('gauge-1');
            } else if (degrees <= 72) {
                indicator.classList.add('gauge-2');
            } else if (degrees <= 108) {
                indicator.classList.add('gauge-3');
            } else if (degrees <= 144) {
                indicator.classList.add('gauge-4');
            } else {
                indicator.classList.add('gauge-5');
            }
        };

        const init = () => {
            container = document.querySelector(selector);

            if (!container) {
                throw new Error(`Gauge container "${selector}" not found`);
            }

            values.min = parseInt(container.dataset.min || '0', 10);
            values.max = parseInt(container.dataset.max || '100', 10);
            values.current = parseInt(
                container.dataset.initial || '0',
                10
            );

            container.classList.add('gauge');

            title = document.createElement('h1');
            title.classList.add('gauge-title');

            indicator = document.createElement('div');
            indicator.classList.add('gauge-indicator');

            container.appendChild(title);
            container.appendChild(indicator);

            update();
        };

        const set = (value) => {
            value = Number(value);

            if (value < values.min) value = values.min;
            if (value > values.max) value = values.max;

            values.current = value;
            update();
        };

        const reset = () => {
            values.current = parseInt(
                container.dataset.initial || '0',
                10
            );

            update();
        };

        init();

        return {
            set,
            reset
        };
    };

    return {
        init(selector) {
            gauges[selector] = createGauge(selector);
        },

        set(selector, value) {
            if (gauges[selector]) {
                gauges[selector].set(value);
            }
        },

        reset(selector) {
            if (gauges[selector]) {
                gauges[selector].reset();
            }
        }
    };
});
// Preview only: loaded before production scripts, never included in build-site output.
(() => {
    const RealDate = Date;
    const instant = new RealDate(2025, 0, 15, 12).getTime();
    class PreviewDate extends RealDate {
        constructor(...args) { super(...(args.length ? args : [instant])); }
        static now() { return instant; }
    }
    window.Date = PreviewDate;
})();

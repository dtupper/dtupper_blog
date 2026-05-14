(function () {
    "use strict";

    function parseLocalDate(value) {
        if (!value) {
            return null;
        }

        var parts = value.slice(0, 10).split("-");
        if (parts.length !== 3) {
            return null;
        }

        var year = Number(parts[0]);
        var month = Number(parts[1]);
        var day = Number(parts[2]);
        if (!year || !month || !day) {
            return null;
        }

        return new Date(year, month - 1, day);
    }

    function daysFromDataset(element, key) {
        var value = Number(element.dataset[key]);
        return Number.isFinite(value) ? value : 7;
    }

    function isRecent(date, days) {
        if (!date) {
            return false;
        }

        var cutoff = new Date();
        cutoff.setHours(0, 0, 0, 0);
        cutoff.setDate(cutoff.getDate() - days);
        return date >= cutoff;
    }

    function showBadge(element, className, label) {
        element.classList.remove("badge-new", "badge-updated");
        element.classList.add(className);
        element.textContent = label;
        element.hidden = false;
    }

    function updateBadge(element) {
        var updated = parseLocalDate(element.dataset.updatedDate);
        var posted = parseLocalDate(element.dataset.postedDate);
        var updatedDays = daysFromDataset(element, "recentlyUpdatedDays");
        var postedDays = daysFromDataset(element, "recentlyPostedDays");

        if (isRecent(updated, updatedDays)) {
            showBadge(element, "badge-updated", "Recently Updated");
        } else if (isRecent(posted, postedDays)) {
            showBadge(element, "badge-new", "New");
        } else {
            element.hidden = true;
        }
    }

    function updateBadges() {
        var badges = document.querySelectorAll("[data-recency-badge]");
        for (var i = 0; i < badges.length; i += 1) {
            updateBadge(badges[i]);
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", updateBadges);
    } else {
        updateBadges();
    }
}());

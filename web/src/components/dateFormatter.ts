
export const DateFormat = {
    DD_MM_YYYY_DOT: "DD.MM.YYYY",
    DD_MM_YYYY_SLASH: "DD/MM/YYYY",
    DD_MM_YYYY_HH_MM_SLASH: "DD/MM/YYYY HH:MM",
    DD_MM_YYYY_HH_MM_DOT: "DD.MM.YYYY HH:MM",
    ISO_YYYY_MM_DD: "YYYY-MM-DD",
} as const;

export type DateFormat = (typeof DateFormat)[keyof typeof DateFormat];

export function formatDate(date: Date, format: DateFormat): string {
    const day = date.getDate().toString().padStart(2, "0");
    const month = (date.getMonth() + 1).toString().padStart(2, "0");
    const year = date.getFullYear();
    
    switch (format) {
        case DateFormat.DD_MM_YYYY_DOT:
            return `${day}.${month}.${year}`;
        case DateFormat.DD_MM_YYYY_SLASH:
            return `${day}/${month}/${year}`;
        case DateFormat.DD_MM_YYYY_HH_MM_SLASH: {
            const hours = date.getHours().toString().padStart(2, "0");
            const minutes = date.getMinutes().toString().padStart(2, "0");
            return `${day}/${month}/${year} ${hours}:${minutes}`;
        }
        case DateFormat.DD_MM_YYYY_HH_MM_DOT: {
            const hours = date.getHours().toString().padStart(2, "0");
            const minutes = date.getMinutes().toString().padStart(2, "0");
            return `${day}.${month}.${year} ${hours}:${minutes}`;
        }
        case DateFormat.ISO_YYYY_MM_DD:
            return `${year}-${month}-${day}`;

        default:
           throw new Error("Unsupported date format: " + format);
    }
}

function constructDateFromParts(dayMonthYearDateParts: string[]): Date {
    if (dayMonthYearDateParts.length !== 3) {
        throw new Error("Expected exactly 3 date parts, but got " + dayMonthYearDateParts.length); 
    }
    const [day, month, year] = dayMonthYearDateParts.map((p) => parseInt(p, 10));
    if (day > 31 || day < 1 || month > 12 || month < 1 || year < 0) {
        throw new Error("Invalid date parts, day: " + day + ", month: " + month + ", year: " + year);
    }
    if (isNaN(day) || isNaN(month) || isNaN(year)) {
        throw new Error("Invalid date parts, not a number, day: " + day + ", month: " + month + ", year: " + year);
    }
    return new Date(year, month - 1, day);
}


export function parseDate(
    dateString: string | null | undefined,
    format: DateFormat
): Date {
    if (!dateString) {
        throw new Error("Date string is required");
    }

    const datePart = dateString.split(" ")[0];
    
    switch (format) {
        case DateFormat.DD_MM_YYYY_DOT:
        case DateFormat.DD_MM_YYYY_HH_MM_DOT: {
            const parts = datePart.split(".");
            return constructDateFromParts(parts);
        }
        case DateFormat.DD_MM_YYYY_SLASH:
        case DateFormat.DD_MM_YYYY_HH_MM_SLASH: {
            const parts = datePart.split("/");
            return constructDateFromParts(parts);
        }
        case DateFormat.ISO_YYYY_MM_DD: {
            const parts = datePart.split("-");
            return constructDateFromParts(parts.reverse());
        }
        default:
            throw new Error("Unsupported date format");
    }
}

export function convertDateFormat(inputDateString: string, fromFormat: DateFormat, toFormat: DateFormat): string {
    const date = parseDate(inputDateString, fromFormat);
    return formatDate(date, toFormat);
}
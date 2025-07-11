import React from 'react';
import { Badge, Calendar } from 'antd';
import './../assets/styles/CustomCalendar.css'

const getListData = (value) => {
    // This helper function is correct as-is.
    switch (value.date()) {
        case 8:
            return [{ type: 'warning', content: 'This is warning event.' }, { type: 'success', content: 'This is usual event.' }];
        case 10:
            return [{ type: 'warning', content: 'This is warning event.' }, { type: 'success', content: 'This is usual event.' }, { type: 'error', content: 'This is error event.' }];
        case 15:
            return [{ type: 'warning', content: 'This is warning event' }, { type: 'success', content: 'This is very long usual event......' }, { type: 'error', content: 'This is error event 1.' }, { type: 'error', content: 'This is error event 2.' }, { type: 'error', content: 'This is error event 3.' }, { type: 'error', content: 'This is error event 4.' }];
        default:
            return [];
    }
};

const getMonthData = (value) => {
    // This helper function is correct as-is.
    if (value.month() === 8) { // September is month 8 (0-indexed)
        return 1394;
    }
    return null;
};


const CustomCalendar = () => {

    // THE FIX: This function now receives the full `info` object.
    // Its job is to render the *entire* cell content for a date.
    const dateCellRender = (current, info) => {
        const listData = getListData(current);
        return (
            <div className="ant-picker-cell-inner">
                {/* We render the original content (the number) first... */}
                {info.originNode}
                {/* ...then we render our list of events below it. */}
                <ul className="events">
                    {listData.map((item, index) => (
                        <li key={`${current.date()}-${index}`}>
                            <Badge status={item.type} text={item.content} />
                        </li>
                    ))}
                </ul>
            </div>
        );
    };

    // This function is for rendering the content of a month cell in the "Year" view.
    const monthCellRender = (value) => {
        const num = getMonthData(value);
        return num ? (
            <div className="notes-month">
                <section>{num}</section>
                <span>Backlog number</span>
            </div>
        ) : null;
    };

    // This main render function now acts as a router.
    // It decides WHICH specific render function to call based on the cell type.
    const cellRender = (current, info) => {
        if (info.type === 'date') {
            // If it's a date cell, pass control to dateCellRender.
            return dateCellRender(current, info);
        }
        if (info.type === 'month') {
            // If it's a month cell, pass control to monthCellRender.
            return monthCellRender(current);
        }

        // For any other case (like 'year' cells), just return the default.
        // This is the crucial fallback.
        return info.originNode;
    };

    return (
        <div style={{ padding: '20px', maxWidth: '1000px', margin: '0 auto' }}>
            <Calendar cellRender={cellRender} style={{ minHeight: '600px' }} />
        </div>
    );
};

export default CustomCalendar;

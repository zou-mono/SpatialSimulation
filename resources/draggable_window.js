// 改变分隔条左右宽度所需常量
let oRoot = document.getElementById("root"),
    oTop = document.getElementById("top_container"),
    oBottom = document.getElementById("bottom_container"),
    oLine = document.getElementById("drag_line");

const splitMinUp = 200; // 分隔条上边部分最小宽度
const splitMaxUp = oRoot.clientHeight - splitMinUp; // 分隔条上边部分最大宽度
const lineWidth = oLine.clientHeight
const upWidth = 200
const bottomToUpGap = oRoot.clientHeight * 0.01; // 下边部分与上边部分的间距

window.onload = function() {
    oLine.onmousedown = handleLineMouseDown;
};

// 分隔条操作
function handleLineMouseDown(e) {
    // 记录初始位置的值
    let disY = e.clientY;
    oLine.up = oLine.offsetTop;

    document.onmousemove = function(e) {
        let moveY = e.clientY - disY; // 鼠标拖动的偏移距离
        let iT = oLine.up + moveY, // 分隔条相对父级定位的 up 值
            maxT = oRoot.clientHeight- oLine.offsetHeight;

        iT < 0 && (iT = 0);
        iT > maxT && (iT = maxT);

        if (iT <= splitMinUp || iT >= splitMaxUp) return false;

        let upLineGap = splitMinUp - upWidth; // 分隔条距上边部分的距离
        let oUpWidth = iT - upLineGap;
        let oBottomMarginTop = oUpWidth + lineWidth + bottomToUpGap;

        oLine.style.top = `${iT}px`;
        oTop.style.height = `${oUpWidth}px`;
        // oBottom.style.marginTop = `${oBottomMarginTop}px`;
        oBottom.style.height = `${oRoot.clientHeight -oUpWidth}px`

        top_chart.resize();
        bottom_chart.resize();
        return false;
    };

    // 鼠标放开的时候取消操作
    document.onmouseup = function() {
        document.onmousemove = null;
        document.onmouseup = null;
    };
}

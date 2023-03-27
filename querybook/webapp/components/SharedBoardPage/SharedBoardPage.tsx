import * as React from 'react';
import { useDispatch, useSelector } from 'react-redux';

import { BoardBoardItem } from 'components/Board/BoardBoardItem';
import { BoardPageContext, IBoardPageContextType } from 'context/BoardPage';
import { fetchSharedBoardIfNeeded } from 'redux/board/action';
import { Dispatch, IStoreState } from 'redux/store/types';
import { AccentText } from 'ui/StyledText/StyledText';

export const SharedBoardPage: React.FunctionComponent = () => {
    const dispatch: Dispatch = useDispatch();

    const board = useSelector((state: IStoreState) => state.board.boardById[-1]);
    React.useEffect(() => {
        dispatch(fetchSharedBoardIfNeeded(-1));
    }, [dispatch]);

    const boardItemDOM = board?.boards?.map((boardId) => (
        <BoardBoardItem boardId={boardId} key={boardId} />
    ));

    const boardContextValue: IBoardPageContextType = React.useMemo(
        () => ({
            onDeleteBoardItem: () => null,
            isEditMode: false,
            isCollapsed: false,
            boardId: -1,
        }),
        []
    );

    return (
        <BoardPageContext.Provider value={boardContextValue}>
            <div className="Board">
                <div className="Board-content">
                    <AccentText
                        className="p8"
                        color="light"
                        size="xlarge"
                        weight="extra"
                    >
                        All Shared Lists
                    </AccentText>
                    {boardItemDOM}
                </div>
            </div>
        </BoardPageContext.Provider>
    );
};

import './index.css';
import './App.css';
import { useState, useEffect } from 'react';
import axios from 'axios';
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function App() {
  const [target, setTarget] = useState('');
  const [numbersText, setNumbersText] = useState('');
  const [result, setResult] = useState('');
  const [lastUsed, setLastUsed] = useState<number[] | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE_URL}/`, { method: "GET" })
      .catch(() => {});
  }, []);

  const handleRunClick = async () => {
    const numbers = numbersText
      .split('\n')
      .map(line => line.trim())
      .filter(line => line !== '')
      .map(Number);

    const targetInt = parseInt(target);

    if (isNaN(targetInt) || numbers.some(n => isNaN(n))) {
      setResult('🔴無効な入力です');
      return;
    }

    if (numbers.length > 50) {
      setResult('🔴数値は50個以内で入力してください');
      return;
    }

    setIsLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/find_combination`, {
        numbers,
        target: targetInt,
      });

      const data = response.data;

      if (data.exact) {
        setResult(`🟢${data.exact.join(' + ')} = ${targetInt}`);
        setLastUsed(data.exact);
      } else if (data.closest) {
        setResult(`🟡${data.closest.join(' + ')} = ${data.closest_sum}`);
        setLastUsed(data.closest);
      } else if (data.message) {
        setResult(`🔴${data.message}`);
        setLastUsed(null);
      } else {
        setResult('🔴予期しないレスポンスです');
        setLastUsed(null);
      }
    } catch (error) {
      console.error(error);
      setResult('🔴通信エラーが発生しました');
    } finally {
      setIsLoading(false);
    }
  };

  const handleOrganizeClick = async () => {
    const numbers = numbersText
      .split('\n')
      .map(line => line.trim())
      .filter(line => line !== '')
      .map(Number);

    if (!lastUsed || lastUsed.length === 0) {
      setResult('🔴整理できる結果がありません．');
      return;
    }

    setIsLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/remove_used_numbers`, {
        numbers,
        used: lastUsed,
      });

      const data = response.data;
      if (data.remaining) {
        setNumbersText(data.remaining.join('\n'));
        setResult('🟢数値リストを整理しました．');
      } else {
        setResult('🔴整理に失敗しました．');
      }
    } catch (error) {
      console.error(error);
      setResult('🔴通信エラーが発生しました');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="header">レシカル</header>
      <div className="main">
        <div className="input-panels">
          <div className="left-panel">
            <div className="input-group">
              <p className="label">目標の値を入力</p>
              <input
                type="text"
                className="panel-input"
                value={target}
                onChange={e => setTarget(e.target.value)}
              />
            </div>
          </div>
          <div className="right-panel">
            <div className="input-group">
              <p className="label">数値を入力 (50個以内)</p>
              <textarea
                className="multi-input"
                value={numbersText}
                onChange={e => setNumbersText(e.target.value)}
              />
              <div className="count-hint">
                {numbersText
                  .split('\n')
                  .map(line => line.trim())
                  .filter(line => line !== '')
                  .length} 個の数値が入力されています
              </div>
            </div>
          </div>
        </div>

        <div className="result-area">
          <p className="label">結果</p>
          <div className="result-output">{result}</div>
        </div>

        <div className="button-wrapper">
          <button className="base-button run-button" onClick={handleRunClick} disabled={isLoading}>
            実行
          </button>
          <button className="base-button organize-button" onClick={handleOrganizeClick} disabled={isLoading}>
            結果をもとに数値リスト整理
          </button>
        </div>
      </div>
      
      <footer className='about'>
        <a href="/about.html" target="_blank" rel="noopener noreferrer">
          レシカルについて
        </a>
      </footer>

      {isLoading && (
        <div className="overlay">
          <div className="spinner"></div>
        </div>
      )}
    </div>
  );
}

export default App;
